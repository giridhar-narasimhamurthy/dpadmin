---
title: SRE Agent - Dpadmin
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
variables:
  API_BASE_URL: "https://router.huggingface.co/v1"
  MODEL_NAME: "Qwen/Qwen2.5-72B-Instruct"
base_path: /web
---

# SRE Autonomous Agent: Dpadmin Environment

This agent is an expert Site Reliability Engineer (SRE) designed to manage infrastructure lifecycle, redundancy, and disaster recovery.
Currently, it learns how to plan proactive data protection, reactive data protection and disaster recovery for an IT infrastructure.
Currently, the environment provides training in 3 tasks:
1. Proactive Data Protection
2. Reactive Data Protection
3. Disaster Recovery

## Configuration Variables
The environment supports 3 tasks:
1. Proactive Data Protection
   This task teaches the agent how to pick data storage protection techniques such as RAID levels. In order to run this task, set environment variable DPADMIN_TASK: "id_setup_redundancy" .
   
2. Reactive Data Protection
   This task teaches the agent how to pick data protection techniques such as snapshots, backups. In order to run this task, set environment variable DPADMIN_TASK: "id_backup_lifecyle" .
   
3. Disaster Recovery
   This task teaches the agent how to pick data recovery techniques such as point-in-time restore. In order to run this task, set environment variable DPADMIN_TASK: "id_dr_recovery" .
   
## Environment Description
The **Dpadmin Environment** is a simulated infrastructure management platform.
The user specifies the IT infrastructure that contains the data assets to be protected in a YAML file. The user also specifies the data protection requirements in another YAML file.
The environment uses these descriptions to train an LLM agent in data protection planning.

**The IT Infrastructure Description File**

This is called *infra.yaml* and is stored in 2 directories:
1. infra_data in the root directory
2. server/model

The contents of *infra.yaml* are:
1. **hosts**


   This specifies the DNS names of systems running applications in the IT infrastructure.

2. **apps**


   This specifies applications that are deployed in the IT infrastructure.

3. **data_storage**


   This specifies the data storage products deployed.

4. **network_connections**


   This specifies network reachability between different hosts.

5. **relationships**


   This specifies the relation between the hosts, applications and storage systems.

6. **classification**


    This specifies the importance of the data created by the applications to the business. This is divided into Tiers where Tier 1 is highest priority and Tier 3 is lowest. Also, "PII/Regulated" is a type of data.

**PLEASE NOTE**: Not all values are currently used.

The contents of *requirements.yaml* are:
1. **Functional Requirement**

   This specifies functionality that is required. These are used to specify requirements such as RPO, RTO, Availability.

3. **Non-Functional Requirements**

  These specify the qualitative requirements.

Each requirement has the format:

[<"functional" | "nonfunctional">, <"mandatory" | "optional">, < description text >]


## Action & Observation Spaces

### **Action Space**
The agent interacts via a Pydantic-validated `DpadminAction` model:

1. **Reactive Data Protection Actions**
   
* `SET_POLICY(target, policy)`:

  
  Configure Snapshot, Backup frequency.

  
  Here *target* is the host/app/storage system as specified in the *infra.yaml*.

  
  Valid *policy* are:

  (a) SNAPSHOT_15MIN: Snapshots every 15 minutes,

  (b) BACKUP_HOURLY: Save backups every 60 minutes

  (c) BACKUP_DAILY: Save backups every 24 hours
  
* `SET_RETENTION(target, days)`:

   Here *target* is the host/app/storage system as specified in the *infra.yaml*.

   *days* refers to the number of days after which a snapshot or a backup must be deleted.

  
2. **Disaster Recovery Actions**
   
* `EXECUTE_RECOVERY(target, params)`: Perform system restoration.

   Here *target* is the host/app/storage system as specified in the *infra.yaml*.

   Valid *params* are POINT_IN_TIME and RESTORE_LATEST.

3. **Proactive Data Protection Actions**
   
* `SET_REDUNDANCY(target, mode)`: Configure RAID/Replication.

  Here *target* is the host/app/storage system as specified in the *infra.yaml*.

  Valid *modes* are:
  (a) None: No data redundancy measures are configured
  
  (b) RAID1: RAID 1 is configure
  
  (c) RAID5: RAID 5 is configured
  
  (d) RAID6: RAID 6 is configured
  
  (e) RAID10: RAID 10 is configured
  
  (e) REPLICATION: replicas are created to another site
  
  (f) REPLICATION+RAID[1/5/6/10]: both redundancy and replication are configured

### **Observation Space**
The environment returns a `DpadminObservation` containing:

**timestamp (str)**: The current simulation time, used for sequencing protection events.

**rpo_gap_min (int)**: Minutes elapsed since the last successful protection event. This is the primary metric for RPO SLA compliance.

**io_latency_ms (float)**: Real-time I/O latency. High values indicate that protection tasks (like backups) are impacting production performance.

**status_code (int)**: Operational status of the target system (1 for ONLINE, 0 for OFFLINE/FAILURE).

**integrity_score (float)**: Data verification status (1.0 is clean, < 1.0 indicates potential data corruption or ransomware signatures).

### **Event Flow**

This is description of how an agent can use our environment to get training in Data Protection.

1. User procide *infra.yaml* and *requirements.yaml* to both the LLM Agent and our environment.
 
2. The agent uses *requirements.yaml* and appropriate prompts to decide data protection actions *for each host, application and data storage system* in the IT infrastructure. 
These actions are specific to the 3 tasks defined currently.

3. The agent passes the action to the environment in step() function.

4. The environment uses the same *infra.yaml* and *requirements.yaml* to determine the ideal reward for agent's actions based on pre-determined rules and simulation logic.
It responds with observation that contains the reward.

6. The agent strives to achieve the highest reward for an action by using feedback in the observation returned.

## Local Setup
If you want to run this locally on your own hardware (e.g., Intel Arc GPU):
1. Install [Ollama](https://ollama.com).
2. Run `ollama run qwen2.5:7b`.
3. Update `inference.py` to use `base_url="http://localhost:11434/v1/"`.
4. Run `python inference.py`.
