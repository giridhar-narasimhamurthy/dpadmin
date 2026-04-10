# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Dpadmin Env Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

try:
    from .models import DpadminAction, DpadminObservation
except ImportError:
    from models import DpadminAction, DpadminObservation

class DpadminEnv(
    EnvClient[DpadminAction, DpadminObservation, State]
):
    """
    Client for the Dpadmin Env Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with DpadminEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.echoed_message)
        ...
        ...     result = client.step(DpadminAction(message="Hello!"))
        ...     print(result.observation.echoed_message)

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = DpadminEnv.from_docker_image("dpadmin_env-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(DpadminAction(message="Test"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: DpadminAction) -> Dict:
        """
        Convert DpadminAction to JSON payload for step message.

        Args:
            action: DpadminAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        """
        Convert DpadminAction (command, target, params) to JSON for the wire.
        """
        return {
            "command": action.command,
            "target": action.target,
            "params": action.params,
        }

    def _parse_result(self, payload: Dict) -> StepResult[DpadminObservation]:
        """
        Parse server response into StepResult[DpadminObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with DpadminObservation
        """
        """
        Parse the server's telemetry response into a DpadminObservation.
        """
        obs_data = payload.get("observation", {})
        resource_health = obs_data.get("resource_health", {})
        observation = DpadminObservation(
            timestamp=obs_data.get("timestamp", ""),
            rpo_gap_min=obs_data.get("rpo_gap_min", 0),
            io_latency_ms=obs_data.get("io_latency_ms", 0.0),
            status_code=obs_data.get("status_code", 1),
            integrity_score=obs_data.get("integrity_score", 1.0),
            resource_health=resource_health,
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
            metadata=payload.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        """
        Parse server response into the OpenEnv State object.
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            # You can optionally include telemetry in metadata here for debugging
            metadata=payload.get("metadata", {}) 
        )
