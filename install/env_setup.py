#!/usr/bin/env python3
"""
Environment Setup Script
Checks environment variables for required tools,
installs missing ones, and creates modulefiles.
Run as root: sudo python3 env_setup.py
"""

import os
import subprocess
import sys
import shutil
import socket

HOSTNAME     = socket.gethostname()
MODULES_BASE = "/home/kaveripk/modules"

# ── Software Registry ─────────────────────────────────────────────────────── #

SOFTWARE = {
    "python3": {
        "binary_path"  : "/usr/bin/python3",
        "binary_dir"   : "/usr/bin",
        "lib_path"     : "/usr/lib/python3",
        "version_cmd"  : "python3 --version",
        "install_cmd"  : "apt-get install -y python3 python3-pip",
        "module_dir"   : "python3",
        "module_name"  : "system",
        "env_vars"     : {
            "PYTHON_HOME": "/usr",
        },
    },
    "gcc": {
        "binary_path"  : "/usr/bin/gcc",
        "binary_dir"   : "/usr/bin",
        "lib_path"     : "/usr/lib/gcc",
        "version_cmd"  : "gcc --version",
        "install_cmd"  : "apt-get install -y gcc g++ gfortran build-essential",
        "module_dir"   : "gcc",
        "module_name"  : "system",
        "env_vars"     : {
            "GCC_HOME": "/usr",
        },
    },
    "openmpi": {
        "binary_path"  : "/usr/bin/mpirun",
        "binary_dir"   : "/usr/bin",
        "lib_path"     : "/usr/lib/x86_64-linux-gnu/openmpi/lib",
        "version_cmd"  : "mpirun --version",
        "install_cmd"  : "apt-get install -y openmpi-bin libopenmpi-dev",
        "module_dir"   : "openmpi",
        "module_name"  : "system",
        "env_vars"     : {
            "MPI_HOME"  : "/usr",
            "MPI_RUN"   : "/usr/bin/mpirun",
        },
    },
    "cmake": {
        "binary_path"  : "/usr/bin/cmake",
        "binary_dir"   : "/usr/bin",
        "lib_path"     : "/usr/lib/cmake",
        "version_cmd"  : "cmake --version",
        "install_cmd"  : "apt-get install -y cmake",
        "module_dir"   : "cmake",
        "module_name"  : "system",
        "env_vars"     : {
            "CMAKE_HOME": "/usr",
        },
    },
    "aocc": {
        "binary_path"  : "/home/kaveripk/aocc-compiler-4.2.0/bin/clang",
        "binary_dir"   : "/home/kaveripk/aocc-compiler-4.2.0/bin",
        "lib_path"     : "/home/kaveripk/aocc-compiler-4.2.0/lib",
        "version_cmd"  : "/home/kaveripk/aocc-compiler-4.2.0/bin/clang --version",
        "install_cmd"  : None,   # manual install only
        "module_dir"   : "aocc",
        "module_name"  : "4.2",
        "env_vars"     : {
            "AOCC_HOME"  : "/home/kaveripk/aocc-compiler-4.2.0",
        },
    },
    "intel": {
        "binary_path"  : "/opt/intel/oneapi/compiler/latest/bin/icx",
        "binary_dir"   : "/opt/intel/oneapi/compiler/latest/bin",
        "lib_path"     : "/opt/intel/oneapi/compiler/latest/lib",
        "version_cmd"  : "/opt/intel/oneapi/compiler/latest/bin/icx --version",
        "install_cmd"  : None,   # manual install only
        "module_dir"   : "intel",
        "module_name"  : "oneapi",
        "env_vars"     : {
            "INTEL_HOME" : "/opt/intel/oneapi",
        },
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────── #

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run(cmd, check=False):
    print(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, check=check)


def is_installed(binary_path):
    return os.path.isfile(binary_path) and os.access(binary_path, os.X_OK)


def get_version(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip().splitlines()[0] if result.stdout.strip() else \
               result.stderr.strip().splitlines()[0]
    except Exception:
        return "unknown"


def write_modulefile(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  ✔ Modulefile created : {path}")


# ── Step 1: Check Environment Variables ───────────────────────────────────── #

def check_env_vars():
    section("Step 1: Checking Environment Variables")
    print(f"  {'Software':<12} {'Env Var':<20} {'Value':<38} {'Status'}")
    print(f"  {'─'*85}")

    missing = []
    for name, cfg in SOFTWARE.items():
        for var, expected_val in cfg["env_vars"].items():
            current = os.environ.get(var, "")
            if current:
                status      = "✔ Set"
                val_display = current[:36]
            else:
                status      = "✘ Not Set"
                val_display = "-"
                missing.append((name, var, expected_val))
            print(f"  {name:<12} {var:<20} {val_display:<38} {status}")

    print(f"  {'─'*85}")
    if missing:
        print(f"\n  ✘ {len(missing)} environment variable(s) not set")
    else:
        print(f"\n  ✔ All environment variables are set")

    return missing


# ── Step 2: Check Binaries ────────────────────────────────────────────────── #

def check_binaries():
    section("Step 2: Checking Binaries")
    print(f"  {'Software':<12} {'Binary':<50} {'Version':<28} {'Status'}")
    print(f"  {'─'*100}")

    missing = []
    for name, cfg in SOFTWARE.items():
        found = is_installed(cfg["binary_path"])
        if found:
            version = get_version(cfg["version_cmd"])[:26]
            status  = "✔ Found"
        else:
            version = "-"
            status  = "✘ Missing"
            missing.append(name)
        print(f"  {name:<12} {cfg['binary_path']:<50} {version:<28} {status}")

    print(f"  {'─'*100}")
    if missing:
        print(f"\n  ✘ Missing: {', '.join(missing)}")
    else:
        print(f"\n  ✔ All binaries found")

    return missing


# ── Step 3: Install Missing Software ──────────────────────────────────────── #

def install_missing(missing_binaries):
    section("Step 3: Installing Missing Software")

    if not missing_binaries:
        print("  ✔ Nothing to install")
        return

    run("apt-get update -y")

    for name in missing_binaries:
        cfg = SOFTWARE[name]
        print(f"\n  [{name}]")

        if cfg["install_cmd"] is None:
            print(f"  ⚠ Cannot auto-install {name} — manual installation required")
            if name == "aocc":
                print("    Download from : https://developer.amd.com/amd-aocc/")
                print("    Extract to    : /home/kaveripk/aocc-compiler-4.2.0/")
            elif name == "intel":
                print("    Download from : https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html")
                print("    Then run      : source /opt/intel/oneapi/setvars.sh")
            continue

        print(f"  Installing {name}...")
        run(cfg["install_cmd"])
        if is_installed(cfg["binary_path"]):
            print(f"  ✔ {name} installed successfully")
        else:
            print(f"  ✘ {name} installation may have failed — check manually")


# ── Step 4: Set Environment Variables ─────────────────────────────────────── #

def set_env_vars():
    section("Step 4: Setting Environment Variables")

    profile_path = "/etc/profile.d/caribou_env.sh"
    export_lines = []

    for name, cfg in SOFTWARE.items():
        if not is_installed(cfg["binary_path"]):
            print(f"  – Skipping {name} (not installed)")
            continue

        for var, val in cfg["env_vars"].items():
            export_lines.append(f"export {var}={val}")
            os.environ[var] = val
            print(f"  ✔ {name:<12} {var}={val}")

        export_lines.append(f"export PATH={cfg['binary_dir']}:$PATH")
        export_lines.append(f"export LD_LIBRARY_PATH={cfg['lib_path']}:$LD_LIBRARY_PATH")
        export_lines.append("")

    # write to /etc/profile.d for system-wide persistence
    content  = "#!/bin/bash\n"
    content += "# Auto-generated by env_setup.py (Caribou)\n\n"
    content += "\n".join(export_lines) + "\n"

    with open(profile_path, "w") as f:
        f.write(content)
    os.chmod(profile_path, 0o755)

    print(f"\n  ✔ Written to : {profile_path}")
    print(f"  ✔ Run 'source {profile_path}' to apply in current shell")


# ── Step 5: Create Modulefiles ────────────────────────────────────────────── #

def create_modulefiles():
    section("Step 5: Creating Modulefiles")

    for name, cfg in SOFTWARE.items():
        if not is_installed(cfg["binary_path"]):
            print(f"  – Skipping {name} (not installed)")
            continue

        mod_path = os.path.join(MODULES_BASE, cfg["module_dir"], cfg["module_name"])

        if os.path.isfile(mod_path):
            print(f"  ✔ Already exists : {mod_path}")
            continue

        # build setenv block
        env_block = ""
        for var, val in cfg["env_vars"].items():
            env_block += f"setenv          {var:<20} {val}\n"

        content = f"""#%Module1.0
# Auto-generated by env_setup.py (Caribou)
# Software : {name}
# Binary   : {cfg['binary_path']}

proc ModulesHelp {{}} {{
    puts stderr "{name} - auto-generated by Caribou env_setup"
    puts stderr "Binary : {cfg['binary_path']}"
    puts stderr "Lib    : {cfg['lib_path']}"
}}

module-whatis "{name} environment"

prepend-path    PATH             {cfg['binary_dir']}
prepend-path    LD_LIBRARY_PATH  {cfg['lib_path']}
{env_block}"""

        write_modulefile(mod_path, content)

    print(f"\n  ✔ All modulefiles written under : {MODULES_BASE}")
    print(f"  Run 'module avail' to see them")


# ── Step 6: Final Status Report ───────────────────────────────────────────── #

def final_report():
    section("Final Status Report")
    print(f"  {'Software':<12} {'Binary':<12} {'Env Vars':<12} {'Modulefile':<12}")
    print(f"  {'─'*50}")

    for name, cfg in SOFTWARE.items():
        binary_ok = "✔" if is_installed(cfg["binary_path"]) else "✘"
        env_ok    = "✔" if all(os.environ.get(v) for v in cfg["env_vars"]) else "✘"
        mod_path  = os.path.join(MODULES_BASE, cfg["module_dir"], cfg["module_name"])
        module_ok = "✔" if os.path.isfile(mod_path) else "✘"
        print(f"  {name:<12} {binary_ok:<12} {env_ok:<12} {module_ok:<12}")

    print(f"  {'─'*50}")


# ── Main ──────────────────────────────────────────────────────────────────── #

def main():
    if os.geteuid() != 0:
        print("ERROR: Must be run as root (sudo python3 env_setup.py)")
        sys.exit(1)

    print("\n" + "="*60)
    print("  Caribou Environment Setup")
    print(f"  Host : {HOSTNAME}")
    print("="*60)

    missing_env  = check_env_vars()
    missing_bins = check_binaries()

    install_missing(missing_bins)
    set_env_vars()
    create_modulefiles()
    final_report()

    print("\n" + "="*60)
    print("  ✔ Environment Setup Complete!")
    print("="*60)
    print(f"\n  To apply in current shell:")
    print(f"    source /etc/profile.d/caribou_env.sh")
    print(f"\n  To load a module:")
    print(f"    module load gcc/system")
    print(f"    module load openmpi/system")
    print(f"    module load python3/system\n")


if __name__ == "__main__":
    main()
