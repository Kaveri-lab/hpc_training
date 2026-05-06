import os
import subprocess

SLURM_BINARIES = {
    "sbatch"    : "/usr/local/bin/sbatch",
    "squeue"    : "/usr/local/bin/squeue",
    "sinfo"     : "/usr/local/bin/sinfo",
    "sacct"     : "/usr/local/bin/sacct",
    "scancel"   : "/usr/local/bin/scancel",
    "scontrol"  : "/usr/local/bin/scontrol",
    "slurmctld" : "/usr/local/sbin/slurmctld",
    "slurmd"    : "/usr/local/sbin/slurmd",
}

def check_slurm_binaries():
    print("\n  SLURM Binary Check")
    print(f"  {'─'*55}")
    print(f"  {'Binary':<15} {'Path':<35} {'Status'}")
    print(f"  {'─'*55}")

    all_found = True
    for name, path in SLURM_BINARIES.items():
        found  = os.path.isfile(path) and os.access(path, os.X_OK)
        status = "✔ Found" if found else "✘ Missing"
        print(f"  {name:<15} {path:<35} {status}")
        if not found:
            all_found = False

    print(f"  {'─'*55}")

    if all_found:
        try:
            version = subprocess.run(
                ["sinfo", "--version"], capture_output=True, text=True
            ).stdout.strip()
        except Exception:
            version = "unknown"
        print(f"\n  ✔ SLURM binaries found — skipping build ({version})")
    else:
        print(f"\n  ✘ SLURM binaries missing — installation required")
        print(f"  Run: sudo python3 caribou.py --setup install")

    return all_found

def run():
    check_slurm_binaries()

if __name__ == "__main__":
    run()
