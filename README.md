---
title: SRE Agent - Dpadmin
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
base_path: /web
---

# SRE Autonomous Agent: Dpadmin Environment

This agent is an expert Site Reliability Engineer (SRE) designed to manage infrastructure lifecycle, redundancy, and disaster recovery.

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
