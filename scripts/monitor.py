import subprocess
import time

DONE = ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]

def get_job_state(job_id):
    ret = subprocess.run(
        ["sacct", "-j", job_id, "--noheader", "--format=State", "--parsable2"],
        capture_output=True, text=True
    )
    if ret.returncode == 0 and ret.stdout.strip():
        state = ret.stdout.strip().splitlines()[0].split("|")[0].strip().upper()
        return state.split()[0]

    ret = subprocess.run(
        ["squeue", "-j", job_id, "--noheader", "--format=%T"],
        capture_output=True, text=True
    )
    if ret.returncode == 0 and ret.stdout.strip():
        return ret.stdout.strip().upper()

    return "UNKNOWN"

def wait_for_job(job_id, app, kind, results_dir, poll=10):
    print(f"Waiting for {app} {kind} job {job_id} ...")
    last_state = ""
    try:
        while True:
            state = get_job_state(job_id)
            if state != last_state:
                print(f"  [{time.strftime('%H:%M:%S')}] {state}")
                last_state = state
            if state in DONE:
                break
            time.sleep(poll)
    except KeyboardInterrupt:
        print(f"Detached from job {job_id}")
        return False

    if last_state == "COMPLETED":
        return True
    else:
        print(f"Job ended with state: {last_state}")
        print(f"Check errors in: {results_dir}")
        return False
