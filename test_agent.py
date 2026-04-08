#
#
#

from client import DpadminEnv
from models import DpadminAction
import requests

def run_step(client, action):
    print(f"\n--- ACTION: {action.command} | Target: {action.target} | Params: {action.params} ---")
    res = client.step(action)
    print(f"Result -> Reward: {res.reward} | Status: {res.observation.status_code} | RPO Gap: {res.observation.rpo_gap_min}m")
    print(f"Dashboard -> Status: {res.observation.status_code} | Integrity: {res.observation.integrity_score} | Reward: {res.reward}")
    return res

with DpadminEnv(base_url="http://localhost:8000").sync() as client:
    
    # =========================================================================
    # TASK 1: id_setup_redundancy (Design & Hardening)
    # =========================================================================
    print("\n" + "="*50 + "\nTASK 1: SETUP REDUNDANCY\n" + "="*50)
    client.reset(task_id="id_setup_redundancy")

    # Step A: Mediocre Choice (RAID 6 is okay, but not Gold Standard for Tier 1)
    run_step(client, DpadminAction(command="SET_REDUNDANCY", target="srv-db-01", params="RAID6"))

    # Step B: Perfect Choice (RAID 10 + Tier 1 Bonus)
    run_step(client, DpadminAction(command="SET_REDUNDANCY", target="srv-db-01", params="RAID10"))

    # Step C: Poor Topology Choice (Local backup for Tier 1)
    run_step(client, DpadminAction(command="SET_TOPOLOGY", target="srv-db-01", params="LOCAL"))

    # Step D: Correct Topology (Hybrid for offsite protection)
    run_step(client, DpadminAction(command="SET_TOPOLOGY", target="srv-db-01", params="HYBRID"))


    # =========================================================================
    # TASK 2: id_backup_lifecycle (SLA & Efficiency)
    # =========================================================================
    print("\n" + "="*50 + "\nTASK 2: BACKUP LIFECYCLE\n" + "="*50)
    client.reset(task_id="id_backup_lifecycle")

    # Step A: SLA Breach (Hourly for a 30-min requirement)
    run_step(client, DpadminAction(command="SET_POLICY", target="PostgreSQL_DB", params="BACKUP_HOURLY"))

    # Step B: Overkill (15-min for a 30-min requirement - Inefficiency penalty)
    run_step(client, DpadminAction(command="SET_POLICY", target="PostgreSQL_DB", params="SNAPSHOT_15MIN"))

    # Step C: Inefficient Level (Full backup instead of Incremental)
    run_step(client, DpadminAction(command="SET_LEVEL", target="PostgreSQL_DB", params="FULL"))

    # Step D: Correct Efficiency (Incremental)
    run_step(client, DpadminAction(command="SET_LEVEL", target="PostgreSQL_DB", params="INCREMENTAL"))

    # Step E: Risky Retention (Short retention for Tier 1)
    run_step(client, DpadminAction(command="SET_RETENTION", target="PostgreSQL_DB", params="5"))

    # Step F: Perfect Retention (30 days for Tier 1)
    run_step(client, DpadminAction(command="SET_RETENTION", target="PostgreSQL_DB", params="30"))


    # =========================================================================
    # TASK 3: id_dr_recovery (Emergency Response)
    # =========================================================================
    print("\n" + "="*50 + "\nTASK 3: DR RECOVERY\n" + "="*50)
    # Note: In a real test, the env would set srv-db-01 to OFFLINE here
    res = client.reset(task_id="id_dr_recovery")

    print(f"INITIAL DR STATE -> Status: {res.observation.status_code} | Integrity: {res.observation.integrity_score}")

    if res.observation.status_code == 0 or res.observation.integrity_score < 1.0:
        print("DISASTER DETECTED")
    else:
        print("Warning: Environment failed to simulate a disaster.")

    # Step A: Unnecessary Recovery (Running recovery on a healthy system)
    run_step(client, DpadminAction(command="EXECUTE_RECOVERY", target="PostgreSQL_DB", params="RESTORE_LATEST"))

    # (Optional: Manually simulate a failure in telemetry if your reset doesn't yet)
    # Step B: Corrective Recovery (Imagine system is now offline/corrupted)
    # run_step(client, DpadminAction(command="EXECUTE_RECOVERY", target="PostgreSQL_DB", params="POINT_IN_TIME"))
