import argparse
import os
import subprocess
import sys

from config import CFG
from compilers import ask_compiler
from compilers.ask_threads import ask_threads
from benchmarks import stream, hpl
from scripts import generate_sbatch, get_log_path, wait_for_job
from scripts.slurm_check import check_slurm_binaries as check_slurm
from postprocess.stream_report import save_table as stream_table
from postprocess.hpl_report import save_table as hpl_table
from postprocess.hpl_report import print_averages
from modules.module_creator import (
    create_stream_module, create_hpl_module,
    create_all_modulefiles, show_module_avail
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def submit(script_path):
    ret = subprocess.run(["sbatch", script_path], capture_output=True, text=True)
    if ret.returncode != 0:
        print(f"sbatch failed: {ret.stderr.strip()}")
        sys.exit(1)
    job_id = ret.stdout.strip().split()[-1]
    return job_id, script_path


def move_script(script_path, app, job_id):
    results_dir = os.path.join(BASE_DIR, CFG["results"][app])
    job_dir = os.path.join(results_dir, str(job_id))
    os.makedirs(job_dir, exist_ok=True)
    dest = os.path.join(job_dir, os.path.basename(script_path))
    if os.path.isfile(script_path):
        os.rename(script_path, dest)
        print(f"Script saved        : {dest}")
    return job_dir


def run_stream(threads=None):
    results_dir = os.path.join(BASE_DIR, CFG["results"]["stream"])

    if threads is None:
        threads = ask_threads()
    else:
        print(f"Threads             : {threads}")

    binary_found = stream.check_binary()

    if binary_found:
        print("[stream] binary found — skipping build")
        run_script = generate_sbatch("stream", None, "run", threads)
        job_id, script_path = submit(run_script)
        job_dir = move_script(script_path, "stream", job_id)
        print(f"Run job submitted   : {job_id}")
        wait_for_job(job_id, "stream", "run", results_dir)
        report = stream_table(
            job_id, threads, "run",
            get_log_path(job_id, "stream", "run"),
            job_dir,
            binary_status="✔ Already Built"
        )
        print(f"Results saved to    : {report}")

    else:
        print("[stream] binary not found — building from source")
        build_script = generate_sbatch("stream", None, "build")
        job_id, script_path = submit(build_script)
        job_dir = move_script(script_path, "stream", job_id)
        print(f"Build job submitted : {job_id}")
        ok = wait_for_job(job_id, "stream", "build", results_dir)
        report = stream_table(
            job_id, threads, "build",
            get_log_path(job_id, "stream", "build"),
            job_dir,
            binary_status="✘ Not Found — Built Now"
        )
        print(f"Results saved to    : {report}")

        if ok:
            run_script = generate_sbatch("stream", None, "run", threads)
            job_id, script_path = submit(run_script)
            job_dir = move_script(script_path, "stream", job_id)
            print(f"Run job submitted   : {job_id}")
            wait_for_job(job_id, "stream", "run", results_dir)
            report = stream_table(
                job_id, threads, "run",
                get_log_path(job_id, "stream", "run"),
                job_dir,
                binary_status="✔ Freshly Built"
            )
            print(f"Results saved to    : {report}")


def run_hpl(compiler=None, threads=None, np=None):
    results_dir = os.path.join(BASE_DIR, CFG["results"]["hpl"])

    if compiler is None:
        compiler = ask_compiler()
    else:
        print(f"Compiler            : {compiler}")
    print("")

    binary_found = hpl.check_binary(compiler)

    if binary_found:
        print(f"[hpl] binary found — skipping build")
        run_script = generate_sbatch("hpl", compiler, "run", threads, np)
        job_id, script_path = submit(run_script)
        job_dir = move_script(script_path, "hpl", job_id)
        print(f"Run job submitted   : {job_id}")
        wait_for_job(job_id, "hpl", "run", results_dir)
        report = hpl_table(
            job_id, compiler, "run",
            get_log_path(job_id, "hpl", "run"),
            job_dir,
            binary_status="✔ Already Built"
        )
        print_averages(job_dir)
        print(f"Results saved to    : {report}")

    else:
        print(f"[hpl] binary not found — building from source")
        build_script = generate_sbatch("hpl", compiler, "build")
        job_id, script_path = submit(build_script)
        job_dir = move_script(script_path, "hpl", job_id)
        print(f"Build job submitted : {job_id}")
        ok = wait_for_job(job_id, "hpl", "build", results_dir)
        report = hpl_table(
            job_id, compiler, "build",
            get_log_path(job_id, "hpl", "build"),
            job_dir,
            binary_status="✘ Not Found — Built Now"
        )
        print(f"Results saved to    : {report}")

        if ok:
            run_script = generate_sbatch("hpl", compiler, "run", threads, np)
            job_id, script_path = submit(run_script)
            job_dir = move_script(script_path, "hpl", job_id)
            print(f"Run job submitted   : {job_id}")
            wait_for_job(job_id, "hpl", "run", results_dir)
            report = hpl_table(
                job_id, compiler, "run",
                get_log_path(job_id, "hpl", "run"),
                job_dir,
                binary_status="✔ Freshly Built"
            )
            print(f"Results saved to    : {report}")


# ── Setup handlers ────────────────────────────────────────────────────────── #

def run_setup(action):
    install_dir = os.path.join(BASE_DIR, "install")
    scripts_dir = os.path.join(BASE_DIR, "scripts")

    if action == "env":
        print("\n======================= ENV SETUP ===========================")
        _run_install_script(os.path.join(install_dir, "env_setup.py"))

    elif action == "slurm":
        print("\n======================= SLURM BINARY CHECK ==================")
        # slurm_check.py is in scripts/ — just call check_slurm_binaries directly
        from scripts.slurm_check import check_slurm_binaries
        check_slurm_binaries()

    elif action == "cleanup":
        print("\n======================= SLURM CLEANUP =======================")
        _run_install_script(os.path.join(scripts_dir, "cleanup.py"))

    elif action == "compiler":
        print("\n======================= COMPILER SETUP =======================")
        _run_install_script(os.path.join(install_dir, "compiler_setup.py"))

    elif action == "all":
        print("\n======================= FULL SETUP ===========================")
        _run_install_script(os.path.join(install_dir, "env_setup.py"))
        _run_install_script(os.path.join(install_dir, "compiler_setup.py"))


def _run_install_script(script_path, needs_root=True):
    if not os.path.isfile(script_path):
        print(f"  ✘ Script not found: {script_path}")
        sys.exit(1)

    if needs_root and os.geteuid() != 0:
        print(f"  ✘ '{os.path.basename(script_path)}' requires root.")
        print(f"  Run: sudo python3 caribou.py --setup {sys.argv[sys.argv.index('--setup') + 1]}")
        sys.exit(1)

    import importlib.util
    spec   = importlib.util.spec_from_file_location("setup_module", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


# ── Main ──────────────────────────────────────────────────────────────────── #

def main():
    parser = argparse.ArgumentParser(
        description="Caribou HPC Benchmark Tool",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--apps",     nargs="+", choices=["stream", "hpl"],
                        help="run benchmarks: stream, hpl")
    parser.add_argument("--slurm",    choices=["check"],
                        help="check slurm binaries and show cluster info")
    parser.add_argument("--modules",  choices=["check", "create", "avail"], default=None,
                        help="manage environment modules")
    parser.add_argument("--setup",    choices=["env", "compiler", "slurm", "cleanup", "all"],
                        default=None,
                        help=(
                            "setup actions:\n"
                            "  env      — check/install env vars and create modulefiles\n"
                            "  compiler — check and setup compilers\n"
                            "  slurm    — check SLURM binaries\n"
                            "  cleanup  — cancel jobs and clean generated files\n"
                            "  all      — run env + compiler setup"
                        ))
    parser.add_argument("--np",       type=int, default=None,
                        help="number of MPI processes (e.g. --np 4)")
    parser.add_argument("--threads",  type=int, default=None,
                        help="thread count (e.g. --threads 4)")
    parser.add_argument("--compiler", choices=["intel", "aocc"], default=None,
                        help="compiler for HPL (e.g. --compiler intel)")
    args = parser.parse_args()

    # ── setup ──
    if args.setup:
        run_setup(args.setup)
        return

    # ── slurm check ──
    if args.slurm == "check":
        check_slurm()
        return

    # ── modules ──
    if args.modules == "check":
        show_module_avail()
        return
    elif args.modules == "create":
        create_all_modulefiles()
        show_module_avail()
        return
    elif args.modules == "avail":
        show_module_avail()
        return

    # ── benchmarks ──
    if not args.apps:
        parser.print_help()
        sys.exit(1)

    for app in args.apps:
        print(f"\n======================= {app.upper()} ===========================")
        if app == "stream":
            run_stream(args.threads)
        elif app == "hpl":
            run_hpl(args.compiler, args.threads, args.np)


if __name__ == "__main__":
    main()
