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

## Configuration Variables
The environment supports 3 tasks:
1. Proactive Data Protection
   This task teaches the agent how to pick data storage protection techniques such as RAID levels. In order to run this task, set environment variable DPADMIN_TASK: "id_setup_redundancy" .
   
2. Reactive Data Protection
   This task teaches the agent how to pick data protection techniques such as snapshots, backups. In order to run this task, set environment variable DPADMIN_TASK: "id_backup_lifecyle" .
   
3. Disaster Recovery
   This task teaches the agent how to pick data recovery techniques such as point-in-time restore. In order to run this task, set environment variable DPADMIN_TASK: "id_dr_recovery" .
   
## Environment Description
The **Dpadmin Environment** is a simulated infrastructure management platform. It provides an API-driven interface to manage:
* **Host Assets:** `srv-prod-01`, `srv-db-01`, `srv-backup-target`
* **Application Assets:** `InventorySystem`, `PostgreSQL_DB`

## Action & Observation Spaces

### **Action Space**
The agent interacts via a Pydantic-validated `DpadminAction` model:
* `SET_POLICY(target, policy)`: Configure RPO/Backup frequency.
* `SET_REDUNDANCY(target, mode)`: Configure RAID/Replication.
* `EXECUTE_RECOVERY(target, params)`: Perform system restoration.

### **Observation Space**
The environment returns a `DpadminObservation` containing:
* **Infrastructure Dashboard:** Real-time status (Online/Offline) and current configurations.
* **Requirements:** Tier-based SLAs for RPO, RTO, and Retention.

## Local Setup
If you want to run this locally on your own hardware (e.g., Intel Arc GPU):
1. Install [Ollama](https://ollama.com).
2. Run `ollama run qwen2.5:7b`.
3. Update `inference.py` to use `base_url="http://localhost:11434/v1/"`.
4. Run `python inference.py`.
