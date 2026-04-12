# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from openenv.core.env_server.types import Action, Observation
from pydantic import Field
from typing import Literal, Dict

"""
Data models for the Dpadmin Env Environment.

The dpadmin_env environment is a simple test environment that echoes back messages.
"""


class DpadminAction(Action):
    """
    Action for the Dpadmin Env environment
    Maps to Preston de Guise's proactive and reactive protection commands.
    """

    command: Literal[
        "SET_REDUNDANCY",
        "SET_POLICY",
        "SET_LEVEL",
        "EXECUTE_RECOVERY",
        "SET_TOPOLOGY",
        "SET_RETENTION",
    ] = Field(..., description="The specific data protection command to execute.")
    target: str = Field(
        ...,
        description="The Resource ID from the SystemMap (e.g., srv-db-01, PostgreSQL_DB).",
    )
    params: str = Field(
        ...,
        description="Configuration value (e.g., RAID10, SNAP_15M, INCREMENTAL, CLOUD_ARCHIVE).",
    )


class DpadminObservation(Observation):
    """
    Observation from the Data Protection Admin environment.
    Provides the current telemetry and SLA status of the infrastructure.
    """

    timestamp: str = Field(default="", description="Current simulation time.")
    rpo_gap_min: int = Field(
        default=0,
        description="Minutes elapsed since the last successful protection event (RPO status).",
    )
    io_latency_ms: float = Field(
        default=0.0,
        description="Current I/O latency, representing the production impact of protection tasks.",
    )
    status_code: int = Field(
        default=1,
        description="Operational status: 1 for ONLINE, 0 for OFFLINE/FAILURE.",
    )
    integrity_score: float = Field(
        default=1.0,
        description="Data verification status: 1.0 is verified/clean, < 1.0 indicates corruption/ransomware.",
    )
    resource_health: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of resource name to its specific status (ONLINE/OFFLINE)",
    )

    # Required by OpenEnv Base Observation
    # done: bool = Field(default=False)
    # reward: float = Field(default=0.0)
    # metadata: Dict[str, Any] = Field(default_factory=dict)
