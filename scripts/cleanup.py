#!/usr/bin/env python3
"""
SLURM Cleanup Script
Removes everything installed by slurm_install.py
Run as root: sudo python3 slurm_cleanup.py
"""

import os
import subprocess
import sys
import shutil

VER       = "24.11.1"
USER_HOME = "/root"


# ── Helpers ───────────────────────────────────────────────────────────────── #

def run(cmd, check=False):
    print(f"  $ {cmd}")
    subprocess.run(cmd, shell=True, check=check)


def remove(path):
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
        print(f"  ✔ Removed file : {path}")
    elif os.path.isdir(path):
        shutil.rmtree(path)
        print(f"  ✔ Removed dir  : {path}")
    else:
        print(f"  – Not found    : {path}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── Step 1: Stop and disable services ─────────────────────────────────────── #

def stop_services():
    section("Step 1: Stop & Disable SLURM/Munge Services")
    for svc in ["slurmd", "slurmctld", "slurmdbd", "munge"]:
        run(f"systemctl stop {svc}")
        run(f"systemctl disable {svc}")
        print(f"  ✔ Stopped & disabled: {svc}")


# ── Step 2: Remove SLURM binaries ─────────────────────────────────────────── #

def remove_slurm_binaries():
    section("Step 2: Remove SLURM Binaries")
    binaries = [
        "/usr/local/bin/sbatch",
        "/usr/local/bin/squeue",
        "/usr/local/bin/sinfo",
        "/usr/local/bin/sacct",
        "/usr/local/bin/scancel",
        "/usr/local/bin/scontrol",
        "/usr/local/bin/srun",
        "/usr/local/bin/salloc",
        "/usr/local/bin/sstat",
        "/usr/local/bin/sreport",
        "/usr/local/bin/sshare",
        "/usr/local/bin/sprio",
        "/usr/local/sbin/slurmctld",
        "/usr/local/sbin/slurmd",
        "/usr/local/sbin/slurmdbd",
        "/usr/local/sbin/slurmstepd",
    ]
    for b in binaries:
        remove(b)


# ── Step 3: Remove SLURM config and logs ──────────────────────────────────── #

def remove_slurm_configs():
    section("Step 3: Remove SLURM Config Files & Logs")
    paths = [
        "/etc/slurm",
        "/var/spool/slurmctld",
        "/var/spool/slurmd",
        "/var/log/slurmctld.log",
        "/var/log/slurmdbd.log",
        "/var/run/slurmctld.pid",
        "/var/run/slurmd.pid",
        f"{USER_HOME}/slurm.conf",
        f"{USER_HOME}/slurmdbd.conf",
        f"{USER_HOME}/cgroup.conf",
    ]
    for p in paths:
        remove(p)


# ── Step 4: Remove SLURM systemd service files ────────────────────────────── #

def remove_slurm_services():
    section("Step 4: Remove SLURM Systemd Service Files")
    service_files = [
        "/usr/local/lib/systemd/system/slurmctld.service",
        "/usr/local/lib/systemd/system/slurmd.service",
        "/usr/local/lib/systemd/system/slurmdbd.service",
        "/usr/local/lib/systemd/system/slurmctld.service.in",
        "/usr/local/lib/systemd/system/slurmd.service.in",
        "/usr/local/lib/systemd/system/slurmdbd.service.in",
    ]
    for f in service_files:
        remove(f)
    run("systemctl daemon-reload")
    print("  ✔ systemd reloaded")


# ── Step 5: Remove SLURM source and build dirs ────────────────────────────── #

def remove_slurm_source():
    section("Step 5: Remove SLURM/hwloc Source & Tarballs")
    paths = [
        f"{USER_HOME}/slurm-{VER}",
        f"{USER_HOME}/slurm-{VER}.tar.bz2",
        f"{USER_HOME}/hwloc-2.11.2",
        f"{USER_HOME}/hwloc-2.11.2.tar.bz2",
    ]
    for p in paths:
        remove(p)


# ── Step 6: Remove Munge ──────────────────────────────────────────────────── #

def remove_munge():
    section("Step 6: Remove Munge")
    paths = [
        "/etc/munge",
        "/usr/local/var/log/munge",
        "/usr/local/var/run/munge",
        "/usr/local/sbin/mungekey",
        "/usr/local/sbin/munge",
        "/usr/local/sbin/unmunge",
        "/usr/local/sbin/remunge",
        "/usr/local/lib/libmunge.so",
        "/usr/local/lib/libmunge.so.2",
        "/usr/local/lib/libmunge.so.2.0.0",
        "/usr/lib/libmunge.so",
        "/usr/lib/libmunge.so.2",
        f"{USER_HOME}/munge-0.5.16",
        f"{USER_HOME}/munge-0.5.16.tar.xz",
    ]
    for p in paths:
        remove(p)

    # remove munge user
    run("userdel -r munge")
    print("  ✔ Removed user: munge")


# ── Step 7: Remove SLURM user ─────────────────────────────────────────────── #

def remove_slurm_user():
    section("Step 7: Remove SLURM User")
    run("userdel -r slurm")
    print("  ✔ Removed user: slurm")


# ── Step 8: Remove MySQL database ─────────────────────────────────────────── #

def remove_slurm_database():
    section("Step 8: Remove SLURM MySQL Database & User")
    run("mysql -u root -e \"DROP DATABASE IF EXISTS slurm_acct_db\"")
    run("mysql -u root -e \"DROP USER IF EXISTS 'slurm'@'localhost'\"")
    run("mysql -u root -e \"FLUSH PRIVILEGES\"")
    print("  ✔ Removed database: slurm_acct_db")
    print("  ✔ Removed MySQL user: slurm@localhost")


# ── Step 9: Remove temp test job files ────────────────────────────────────── #

def remove_temp_files():
    section("Step 9: Remove Temp Test Job Files")
    import glob
    for f in glob.glob("/tmp/slurm_test*"):
        remove(f)


# ── Main ──────────────────────────────────────────────────────────────────── #

def main():
    if os.geteuid() != 0:
        print("ERROR: Must be run as root (sudo python3 slurm_cleanup.py)")
        sys.exit(1)

    print("\n" + "="*60)
    print("  SLURM Cleanup Script")
    print("  This will remove EVERYTHING installed by slurm_install.py")
    print("="*60)

    confirm = input("\n  Are you sure? This cannot be undone. (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  Aborted.")
        sys.exit(0)

    stop_services()
    remove_slurm_binaries()
    remove_slurm_configs()
    remove_slurm_services()
    remove_slurm_source()
    remove_munge()
    remove_slurm_user()
    remove_slurm_database()
    remove_temp_files()

    print("\n" + "="*60)
    print("  ✔ Cleanup Complete — SLURM fully removed")
    print("="*60)


if __name__ == "__main__":
    main()
