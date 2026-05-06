import os
import subprocess
import sys

COMPILERS = {
    "gcc":   ("/usr/bin/gcc",                                  "gcc/system"),
    "intel": ("/opt/intel/oneapi/compiler/latest/bin/icx",     "intel/oneapi"),
    "aocc":  ("/home/kaveripk/aocc-compiler-4.2.0/bin/clang",  "aocc/4.2"),
    "mpi":   ("/opt/intel/oneapi/mpi/2021.17/bin/mpirun",      "openmpi/system"),
}

# module init script location on your system
MODULE_INIT = "/usr/share/modules/init/bash"


def binary_exists(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)


def run_module_cmd(action, module_name=""):
    """
    Run a module command by sourcing the module init script first.
    This is needed because 'module' is a shell function, not a binary.
    """
    cmd = f"source {MODULE_INIT} 2>/dev/null && module {action} {module_name} 2>&1"
    ret = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True, text=True
    )
    return ret.returncode, ret.stdout, ret.stderr


def module_available(module_name):
    """Check if a module exists by running module avail."""
    code, out, err = run_module_cmd("avail", module_name)
    combined = out + err
    return module_name in combined


def load_module(module_name):
    """Load module and apply env changes to current process."""
    # get env before
    env_before = os.environ.copy()

    # load module and print env after
    cmd = f"source {MODULE_INIT} 2>/dev/null && module load {module_name} 2>/dev/null && env"
    ret = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True)

    if ret.returncode != 0:
        return False

    # apply new/changed env vars to current process
    for line in ret.stdout.splitlines():
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if key and key not in ("_", "SHLVL", "PWD"):
                os.environ[key] = val

    return True


def check_all():
    print("\n  Compiler status")
    print(f"  {'─'*60}")
    print(f"  {'Name':<10} {'Binary':<10} {'Module':<20} {'Path'}")
    print(f"  {'─'*60}")

    results = {}
    for name, (path, module) in COMPILERS.items():
        found  = binary_exists(path)
        mod_ok = module_available(module)
        b_str  = "found" if found else "missing"
        m_str  = "available" if mod_ok else "not found"
        p_str  = path if found else "-"
        print(f"  {name:<10} {b_str:<10} {m_str:<20} {p_str}")
        results[name] = {
            "binary":   found,
            "module":   mod_ok,
            "path":     path,
            "mod_name": module
        }

    print(f"  {'─'*60}")
    return results


def setup(compiler=None):
    results = check_all()
    targets = [compiler] if compiler else list(COMPILERS.keys())

    print("\n  Setting up compilers...")
    all_ok = True

    for name in targets:
        info = results[name]
        print(f"\n  [{name}]")

        if not info["binary"]:
            print(f"  Binary NOT found: {info['path']}")
            print(f"  Install instructions:")
            _install_instructions(name)
            all_ok = False
            continue

        print(f"  Binary found: {info['path']}")

        if info["module"]:
            print(f"  Loading module: {info['mod_name']}")
            ok = load_module(info["mod_name"])
            if ok:
                print(f"  Module loaded successfully")
            else:
                print(f"  Could not load module, using binary directly")
        else:
            print(f"  Module not in module system, using binary directly")

    print()
    if all_ok:
        print("  All compilers ready.")
    else:
        print("  Some compilers are missing. Install them and run again.")
        sys.exit(1)


def _install_instructions(name):
    instructions = {
        "gcc": (
            "    sudo apt install gcc g++ gfortran"
        ),
        "intel": (
            "    Download Intel oneAPI from:\n"
            "    https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html\n"
            "    Then: source /opt/intel/oneapi/setvars.sh"
        ),
        "aocc": (
            "    Download AOCC from:\n"
            "    https://developer.amd.com/amd-aocc/\n"
            "    Extract to: /home/kaveripk/aocc-compiler-4.2.0/"
        ),
        "mpi": (
            "    sudo apt install openmpi-bin libopenmpi-dev"
        ),
    }
    print(instructions.get(name, f"    Check documentation for {name}"))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="check all compilers and print status")
    parser.add_argument("--setup", action="store_true",
                        help="check and load modules, stop if binary missing")
    parser.add_argument("--compiler", choices=list(COMPILERS.keys()), default=None,
                        help="target a specific compiler only")
    args = parser.parse_args()

    if args.check:
        check_all()
    elif args.setup:
        setup(compiler=args.compiler)
    else:
        parser.print_help()
