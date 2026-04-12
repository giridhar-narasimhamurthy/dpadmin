#
# Copyright (c) 2026, Giridhar Narasimhamurthy. All rights reserved.
# Use is subject to license terms.
#

import re
from datetime import datetime, timedelta
from typing import Dict, Any

"""
simulation_time: global timestamp for the episode
"""


class ActiveTelemetry:
    def __init__(self, system_map):
        self.system_map = system_map
        self.simulation_time = datetime.now()
        self.resource_states = {}

        # Initialize state for all apps and storage from SystemMap
        # This ensures we have a dynamic record for every static asset
        all_resources = set(
            list(system_map.apps.keys())
            + list(system_map.data_storage.keys())
            + list(system_map.hosts.keys())
        )
        for res in all_resources:
            app_info = system_map.apps.get(res, {})
            change_rate = app_info.get("daily_change_percent", 0.0)
            self.resource_states[res] = {
                "status": "ONLINE",
                "last_backup_timestamp": self.simulation_time - timedelta(days=1),
                "io_latency_ms": 2.0,
                "storage_utilization_gb": 100.0,
                "current_redundancy": "NONE",
                "current_topology": "LOCAL",  # Default
                "active_policy": "NONE",
                "backup_level": "NONE",  # Default
                "retention_years": 0,  # Default
                "integrity_verified": True,
                "num_replicas": 0,
                "data_change_rate": change_rate,
                "dedup_ratio": 0,
            }

    def advance_time(self, minutes: int):
        """Advances the internal simulation clock."""
        self.simulation_time += timedelta(minutes=minutes)

    def get_rpo_gap(self, resource_id: str) -> int:
        """Calculates current RPO gap in minutes for a specific resource."""
        if resource_id not in self.resource_states:
            return 0
        last_backup = self.resource_states[resource_id]["last_backup_timestamp"]
        delta = self.simulation_time - last_backup
        return int(delta.total_seconds() / 60)

    def _get_params_from_str(self, params: str):
        ret_period_years = 1
        dedup = 1.0

        if isinstance(params, str):
            period_match = re.search(r"retention_period=(\d+)", params)
            dedupe_match = re.search(r"dedup_ratio=([\d\.]+)", params)
            if period_match:
                ret_period_years = int(period_match.group(1))

            if dedupe_match:
                dedup = float(dedupe_match.group(1))

        return ret_period_years, dedup

    def perform_action(self, action_dict: Dict):
        """Updates internal state based on Agent Keywords, resolving Hosts to Apps."""
        cmd = action_dict.get("command")
        raw_target = action_dict.get("target")
        params = action_dict.get("params")

        # 1. Resolve Target
        resolved_app = None
        if raw_target in self.system_map.apps:
            resolved_app = raw_target
        else:
            for rel in self.system_map.relationships:
                if raw_target == rel[1] or raw_target == rel[2]:
                    resolved_app = rel[0]
                    break

        # 2. Update State with Side Effects
        if resolved_app and resolved_app in self.resource_states:
            state = self.resource_states[resolved_app]

            if cmd == "SET_REDUNDANCY":
                state["current_redundancy"] = params
                state["io_latency_ms"] += 5.0

            elif cmd == "SET_TOPOLOGY":
                state["current_topology"] = params
                # Scenario: REMOTE/HYBRID adds network latency compared to LOCAL
                if params in ["REMOTE", "CLOUD", "HYBRID"]:
                    state["io_latency_ms"] += 10.0
                else:
                    state["io_latency_ms"] = max(2.0, state["io_latency_ms"] - 5.0)

            elif cmd == "SET_POLICY":
                state["active_policy"] = params
                state["last_backup_timestamp"] = self.simulation_time

            elif cmd == "SET_LEVEL":
                state["backup_level"] = params
                # FULL backups increase storage utilization significantly
                if params == "FULL":
                    state["storage_utilization_gb"] += 50.0
                elif params == "INCREMENTAL":
                    state["storage_utilization_gb"] += 5.0

            elif cmd == "EXECUTE_RECOVERY":
                state["status"] = "ONLINE"
                state["integrity_verified"] = True
                state["io_latency_ms"] += 20.0

            # Add SET_RETENTION for completeness
            elif cmd == "SET_RETENTION":
                if params is not None:
                    retention_period, dedup_ratio =\
                        self._get_params_from_str(params)
                else:
                    retention_period, dedup_ratio = 1, 1.0

                state["retention_years"] = retention_period
                state["dedup_ratio"] = dedup_ratio
        else:
            # print(f"Warning: Action target '{raw_target}' could not be mapped to a managed App.")
            pass

    def generate_observation_for_agent(self, resource_id: str) -> Dict[str, Any]:
        """
        Maps the internal state to the DpadminObservation schema.
        This is what the Environment class calls to return data to the LLM.
        """
        # Default to the first app if resource_id is invalid
        if resource_id not in self.resource_states:
            resource_id = self.system_map.apps[0]

        state = self.resource_states[resource_id]

        return {
            "rpo_gap_min": self.get_rpo_gap(resource_id),
            "latency": state["io_latency_ms"],
            "status_code": 1 if state["status"] == "ONLINE" else 0,
            "integrity": 1.0 if state["integrity_verified"] else 0.0,
        }
