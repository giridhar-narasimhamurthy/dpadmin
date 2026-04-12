#
# Copyright (c) 2026, Giridhar Narasimhamurthy. All rights reserved.
# Use is subject to license terms.
#


from .ActiveTelemetry import ActiveTelemetry

try:
    from ..models import DpadminAction
except ImportError:
    from models import DpadminAction


class DataProtectionGrader:
    def __init__(self, design_doc, system_map):
        self.design_doc = design_doc
        self.system_map = system_map

    def _grade_setup_redundancy(self, action: DpadminAction) -> float:
        """Logic for Task 1: Hardening and Topology Design."""
        tier = self._get_tier_for_resource(action.target)
        cmd = action.command
        params = action.params

        # --- Sub-Task: RAID/Redundancy Selection ---
        if cmd == "SET_REDUNDANCY":
            scores = {
                "NONE": 0.0,
                "RAID0": 0.0,
                "RAID1": 0.1,
                "RAID5": 0.3,
                "RAID6": 0.4,
                "RAID10": 0.5,
                "REPLICATION": 0.6,
                "REPLICATION+RAID10": 1.0,
            }
            base_score = scores.get(params, 0.0)

            # Tier 1 requires at least RAID 10 for full points
            if tier == "Tier 1" and params in ["RAID10", "REPLICATION+RAID10"]:
                return base_score + 0.4
            return base_score

        # --- Sub-Task: Topology Design ---
        elif cmd == "SET_TOPOLOGY":
            # Logic: Higher Tiers require geographically dispersed data
            topology_scores = {
                "LOCAL": 0.1,  # Single point of failure
                "REMOTE": 0.5,  # Off-site but manual
                "CLOUD": 0.6,  # Off-site managed
                "HYBRID": 1.0,  # Best of both (local speed + cloud safety)
            }
            base_score = topology_scores.get(params, 0.0)

            # Penalty: Tier 1 cannot be "LOCAL" only
            if tier == "Tier 1" and params == "LOCAL":
                return -0.5

            return base_score

        # Irrelevant command for this task
        return -0.1

    def _grade_backup_lifecycle(self, action) -> float:
        tier = self._get_tier_for_resource(action.target)
        cmd = action.command
        params = action.params

        # 1. Requirements (Usually from self.design_doc)
        requirements = {
            "Tier 1": {"rpo": 30, "retention_days": 30},
            "Tier 2": {"rpo": 240, "retention_days": 14},
            "Tier 3": {"rpo": 1440, "retention_days": 7},
        }
        req = requirements.get(tier, requirements["Tier 3"])

        # --- SET_POLICY (Frequency) ---
        if cmd == "SET_POLICY":
            policy_minutes = {
                "SNAPSHOT_15MIN": 15,
                "BACKUP_HOURLY": 60,
                "BACKUP_DAILY": 1440,
            }
            chosen_rpo = policy_minutes.get(params, 99999)
            if chosen_rpo > req["rpo"]:
                return -1.0  # Breach

            if chosen_rpo <= req["rpo"]:
                return 1.0  # Perfect

            # return 0.3 # Inefficient Overkill

        # --- SET_LEVEL (Method) ---
        elif cmd == "SET_LEVEL":
            level_scores = {"INCREMENTAL": 0.8, "DIFFERENTIAL": 0.5, "FULL": 0.3}
            return level_scores.get(params, 0.0)

        return -0.1  # Irrelevant command

    def _grade_dr_recovery(self, action, telemetry: ActiveTelemetry) -> float:
        """Logic for Task 3: Disaster Recovery."""
        target = action.target
        cmd = action.command
        params = action.params

        # Resolve the target to the App to check its current health
        app_id = self._get_app_for_target(target)
        state = telemetry.resource_states.get(app_id, {})

        is_broken = state.get("status") != "ONLINE" or not state.get(
            "integrity_verified"
        )

        if cmd == "EXECUTE_RECOVERY":
            if is_broken:
                # Success: The agent applied a fix to a broken system
                # We reward based on the recovery mode
                if params == "POINT_IN_TIME":
                    return 1.0  # Safe, standard recovery
                elif params == "RESTORE_LATEST":
                    return 0.8  # Good, but might carry over corruption
                return 0.5  # Generic recovery
            else:
                # Penalty: Attempting to 'recover' a system that is already fine
                # This causes unnecessary downtime/cost in the real world
                return -0.5

        # If they try to set policies while the system is down, it's a distraction
        if is_broken and cmd != "EXECUTE_RECOVERY":
            return -0.2

        return 0.0

    def _grade_retention_policy(self, action, telemetry: ActiveTelemetry) -> float:
        target = action.target
        cmd = action.command
        # params = action.params

        # Resolve the target to the App to check its current health
        appid = self._get_app_for_target(target)
        state = telemetry.resource_states.get(target, {})

        if cmd == "SET_RETENTION":
            configured_raid = self._get_raid_multiplier(state["current_redundancy"])
            capacity = self._get_capacity_of_target(target)
            num_replication_sites = state["num_replicas"]
            retention_years = self._get_app_state_property(
                appid, telemetry, "retention_years"
            )
            daily_change_rate = self._get_app_config_property(
                appid, "daily_change_percent"
            )

            dedup_ratio = self._get_app_state_property(appid, telemetry, "dedup_ratio")
            snapshot_pool_percent = 0.25
            reward, _ = self.calculate_cost_reward(
                capacity,
                configured_raid,
                num_replication_sites,
                int(retention_years),
                daily_change_rate,
                dedup_ratio,
                snapshot_pool_percent,
            )
            return reward

        return 0.0

    def _get_raid_multiplier(self, configured_raid: str) -> float:
        raid_map = {
            "NONE": 1.0,
            "RAID0": 1.0,  # No overhead, just striping
            "RAID1": 2.0,  # 100% overhead (Mirror)
            "RAID10": 2.0,  # 100% overhead (Mirror + Stripe)
            "RAID5": 1.33,  # ~33% overhead (Parity)
            "RAID6": 1.5,  # ~50% overhead (Dual Parity)
        }

        return raid_map.get(configured_raid, 1.0)

    def _get_capacity_of_target(self, resource_id) -> float:
        """
        only hosts have capacity mentioned. if target is an app, then find its
        host and return that host's capacity
        """
        if resource_id in self.system_map.hosts:
            return self.system_map.hosts[resource_id].get("total_capacity_gb", 0.0)

        if resource_id in self.system_map.apps:
            for rel in self.system_map.relationships:
                if resource_id == rel[0]:
                    hostid = rel[1]
                    host_data = self.system_map.hosts.get(hostid, {})
                    return host_data.get("total_capacity_gb", 0.0)

        return 0.0

    # fetch properties configured only for apps AND from config file
    def _get_app_config_property(self, resource_id: str, _property: str) -> float:
        if resource_id in self.system_map.apps:
            return self.system_map.apps[resource_id].get(_property, 0.0)

        if resource_id in self.system_map.hosts:
            for rel in self.system_map.relationships:
                if resource_id == rel[1]:
                    appid = rel[0]
                    app_data = self.system_map.apps.get(appid, {})
                    return app_data.get(_property, 0.0)

        return 0.0

    def _get_app_state_property(self, appid, telemetry, _property) -> float:
        state = telemetry.resource_states.get(appid, {})
        return state.get(_property, 0.0)

    def _get_app_for_target(self, target: str) -> str:
        """Helper to ensure we are checking the health of the Application."""
        if target in self.system_map.apps:
            return target
        for rel in self.system_map.relationships:
            if target == rel[1] or target == rel[2]:
                return rel[0]
        return target

    def calculate_step_reward(
        self,
        current_task_id: str,
        action,
        pre_action_telemetry: ActiveTelemetry,
        post_action_telemetry: ActiveTelemetry,
    ) -> float:
        """Main entry point for grading a specific agent action."""

        # Dispatch to the specific task handler
        if current_task_id == "id_setup_redundancy":
            return self._grade_setup_redundancy(action)
        elif current_task_id == "id_backup_lifecycle":
            return self._grade_backup_lifecycle(action)
        elif current_task_id == "id_dr_recovery":
            return self._grade_dr_recovery(action, pre_action_telemetry)
        elif current_task_id == "id_setup_retention":
            return self._grade_retention_policy(action, post_action_telemetry)

        return 0.0

    def get_task_score(self, task_id: str, telemetry: ActiveTelemetry) -> float:
        """
        Final Grader for the 3 OpenEnv Tasks (Returns 0.0 - 1.0).
        """
        if task_id == "id_setup_redundancy":
            # Score based on % of Tier 1 apps having RAID10/6
            tier1_apps = [
                k
                for k, v in self.system_map.data_classification.items()
                if v == "Tier 1"
            ]
            protected = [
                a
                for a in tier1_apps
                if telemetry.resource_states[a]["current_redundancy"]
                in ["RAID10", "RAID6"]
            ]
            return len(protected) / len(tier1_apps) if tier1_apps else 1.0

        if task_id == "id_dr_recovery":
            # Score 1.0 if status is ONLINE and integrity is True
            # Score 0.0 if still OFFLINE at the end of episode
            results = [
                1.0 if s["status"] == "ONLINE" and s["integrity_verified"] else 0.0
                for s in telemetry.resource_states.values()
            ]
            return sum(results) / len(results)

        return 0.0

    def _get_tier_for_resource(self, res_id):
        """Helper to resolve physical ID to App Tier."""
        # 1. Direct App Check
        if res_id in self.system_map.data_classification:
            return self.system_map.data_classification[res_id]

        # 2. Relationship Check (Host/Storage -> App -> Tier)
        for rel in self.system_map.relationships:
            if res_id == rel[1] or res_id == rel[2]:
                app_name = rel[0]
                return self.system_map.data_classification.get(app_name, "Tier 3")

        return "Tier 3"

    def calculate_cost_reward(
        self,
        presented_gb: float,
        raid_multiplier: float,  # From SET_REDUNDANCY
        replication_sites: int,  # From SET_TOPOLOGY
        retention_years: int,  # From Requirements mapping
        daily_change_rate: float,
        dedupe_ratio: float,  # Agent's choice
        snapshot_pool_percent: float = 0.25,
    ):
        # 1. Primary Footprint (RAID * Sites + Snapshots)
        primary_per_site = presented_gb * raid_multiplier
        snapshot_per_site = (presented_gb * snapshot_pool_percent) * raid_multiplier
        total_primary = (primary_per_site + snapshot_per_site) * replication_sites

        # 2. Backup Footprint (Weekly Fulls + Daily Incremental + Monthly Archive)
        # Using de Guise's 5-week short term + 12 monthly per year long term
        weekly_footprint = (
            presented_gb + (presented_gb * (daily_change_rate / 100) * 6)
        ) * 5
        monthly_backups_total = presented_gb * 12 * retention_years

        # Apply Dedupe and Redundancy
        total_backup = ((weekly_footprint + monthly_backups_total) / dedupe_ratio) * 2
        total_footprint = total_primary + total_backup
        multiplier = total_footprint / presented_gb

        # --- REWARD LOGIC ---
        # Goal: Meet the retention requirement with the lowest multiplier.
        # If the agent ignores dedupe for Tier-1 data, the multiplier is ~180x (Too expensive!)
        # If the agent uses 10:1 dedupe, the multiplier drops significantly.

        if multiplier > 200:  # Extremely wasteful
            return 0.2, multiplier
        elif multiplier < 50:  # Efficient but safe
            return 1.5, multiplier
        else:  # Acceptable
            return 1.0, multiplier
