# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Dpadmin Env Environment Implementation.

A simple test environment that echoes back messages sent to it.
Perfect for testing HTTP server infrastructure.
"""

import os
import copy
from uuid import uuid4
from datetime import datetime

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

# Data Protection Model Imports
from .model.SystemMap import SystemMap
from .model.DesignDocument import DesignDocument
from .model.ActiveTelemetry import ActiveTelemetry
from .model.DataProtectionGrader import DataProtectionGrader

try:
    from ..models import DpadminAction, DpadminObservation
except ImportError:
    from models import DpadminAction, DpadminObservation


class DpadminEnvironment(Environment):
    """
    """
    # Enable concurrent WebSocket sessions.
    # Set to True if your environment isolates state between instances.
    # When True, multiple WebSocket clients can connect simultaneously, each
    # getting their own environment instance (when using factory mode in app.py).
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        """Initialize the dpadmin_env environment."""
        # 1. Base OpenEnv State
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        # 2. Load Static Models (Infrastructure & Rules)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        infra_path = os.path.join(BASE_DIR, "model", "infra.yaml")
        self.system_map = SystemMap()
        self.system_map.load_from_yaml(infra_path)
        
        dd_path = os.path.join(BASE_DIR, "model", "requirements.yaml")
        self.design_doc = DesignDocument()
        self.design_doc.load_from_yaml(dd_path)
        
        # 3. Initialize Dynamic Simulation Components
        self.telemetry = ActiveTelemetry(self.system_map)
        self.grader = DataProtectionGrader(self.design_doc, self.system_map)

        self.current_task_id = "id_setup_redundancy"


    def reset(self, task_id: str = None) -> DpadminObservation:
        """
        Reset the environment and simulate realistic failure conditions for DR tasks.
        """
        self._state = State(episode_id=str(uuid4()), step_count=0)
        if task_id:
            self.current_task_id = task_id

        # 1. Fresh telemetry
        self.telemetry = ActiveTelemetry(self.system_map)

        # 2. Dynamic DR Failure Injection
        if self.current_task_id == "id_dr_recovery":
            # Find ANY Tier 1 application dynamically
            tier_1_apps = [
                    app for app, tier in self.system_map.data_classification.items() 
                    if tier == "Tier 1"
                ]

            if tier_1_apps:
                target_app = tier_1_apps[0] # Pick the first Tier 1 app found
                state = self.telemetry.resource_states[target_app]

                # Inject Failure
                state["status"] = "OFFLINE"
                state["integrity_verified"] = False
                state["io_latency_ms"] = 0.0
                print(f"--- [DR SIMULATION] Critical Resource '{target_app}' FAILURE detected ---")
            else:
                print("Warning: No Tier 1 apps found to simulate DR failure.")

        # 3. Global Infrastructure Observation
        # Instead of one app, we generate a summary observation
        return self.generate_global_observation()

    def generate_global_observation(self) -> DpadminObservation:
        """
        Aggregates the health of the entire infrastructure into a single observation.
        """
        all_states = self.telemetry.resource_states.values()
    
        # Calculate global metrics
        # If any resource is OFFLINE, status_code is 0 (System Degraded/Down)
        global_status = 1 if all(s["status"] == "ONLINE" for s in all_states) else 0
        # Map Local Statuses
        local_health = {name: s["status"] for name, s in self.telemetry.resource_states.items()}

        # Average integrity across all apps
        avg_integrity = sum(1.0 if s["integrity_verified"] else 0.0 for s in all_states) / len(all_states)
    
        # Maximum RPO gap found in the fleet (The "Worst Case" gap)
        max_rpo_gap = max(self.telemetry.get_rpo_gap(app) for app in self.system_map.apps)
    
        # Average Latency
        avg_latency = sum(s["io_latency_ms"] for s in all_states) / len(all_states)

        return DpadminObservation(
            timestamp=str(self.telemetry.simulation_time),
            rpo_gap_min=max_rpo_gap,
            io_latency_ms=round(avg_latency, 2),
            status_code=global_status,
            integrity_score=round(avg_integrity, 2),
            resource_health=local_health,
            done=False,
            reward=0.0
        )

    def step(self, action: DpadminAction) -> DpadminObservation:  # type: ignore[override]
        """
        Execute a data protection command and advance the simulation.

        Args:
            action: DpadminAction containing the message to echo

        Returns:
            DpadminObservation with the echoed message and its length
        """
        self._state.step_count += 1
        
        # 1. Map DpadminAction to the Simulation Engine
        action_dict = {
            "command": action.command,
            "target": action.target,
            "params": action.params
        }

        pre_action_telemetry = copy.deepcopy(self.telemetry)

        # 2. Update Infrastructure State
        self.telemetry.perform_action(action_dict)

        # 3. Advance Simulation Time (Tick)
        # We advance 30 minutes to see if the policy holds
        self.telemetry.advance_time(30)
 
        # 4. Calculate Rewards
        step_reward = self.grader.calculate_step_reward(self.current_task_id,
                                                        action,
                                                        pre_action_telemetry)
        
        # 5. Determine Completion (Example: 20 steps per episode)
        is_solved = (step_reward >= 1.0)
        done = self._state.step_count >= 20 or is_solved
        
        # 6. Generate Observation for the target of the action
        obs_data = self.telemetry.generate_observation_for_agent(action.target)

        try:
            health_status = self.telemetry.resource_states[action.target].get("status", "UNKNOWN")

            ret_obs = DpadminObservation(
                timestamp=str(self.telemetry.simulation_time),
                rpo_gap_min=obs_data["rpo_gap_min"],
                io_latency_ms=obs_data["latency"],
                status_code=obs_data["status_code"],
                integrity_score=obs_data["integrity"],
                resource_health={action.target: health_status},
                done=done,
                reward=step_reward,
                metadata={
                    "task": self.current_task_id,
                    "step": self._state.step_count,
                    "target_resource": action.target
                }
            )
        except Exception as e:
            health_status = "ERROR"
            ret_obs = DpadminObservation(
                timestamp=str(self.telemetry.simulation_time),
                rpo_gap_min=obs_data["rpo_gap_min"],
                io_latency_ms=obs_data["latency"],
                status_code=obs_data["status_code"],
                integrity_score=obs_data["integrity"],
                resource_health={action.target: health_status},
                done=done,
                reward=step_reward,
                metadata={
                    "task": self.current_task_id,
                    "step": self._state.step_count,
                    "target_resource": action.target
                }
            )
            print(f"step error: {e}")

        return ret_obs 

    @property
    def state(self) -> State:
        """
        Get the current environment state.

        Returns:
            Current State with episode_id and step_count
        """
        self._state.metadata = self.telemetry.resource_states
        return self._state

    def get_current_score(self) -> float:
        """Helper to expose the 0.0-1.0 grader score."""
        return self.grader.get_task_score(self.current_task_id, self.telemetry)
