import os
import stat
from config import CFG, STREAM_CFG, HPL_CFG
from benchmarks import stream, hpl

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_log_path(job_id, app, kind):
    results_dir = os.path.join(BASE_DIR, CFG["results"][app])
    return os.path.join(results_dir, str(job_id), f"{kind}.out")

def generate_sbatch(app, compiler, kind, threads=None, np=None):
    results_dir = os.path.join(BASE_DIR, CFG["results"][app])
    os.makedirs(results_dir, exist_ok=True)
    job_dir = os.path.join(results_dir, "%j")
    out = os.path.join(job_dir, f"{kind}.out")
    err = os.path.join(job_dir, f"{kind}.err")

    # get slurm settings and command from the correct yaml
    if app == "stream":
        module = STREAM_CFG["build"]["module"]
        ntasks = STREAM_CFG["slurm"]["ntasks"]
        cpus   = STREAM_CFG["slurm"]["cpus_per_task"]
        time   = STREAM_CFG["slurm"]["time"]
        cmd    = stream.get_run_cmd(threads) if kind == "run" else stream.get_build_cmd()
        binary = STREAM_CFG["binary"]
    else:
        module = HPL_CFG["compilers"][compiler]["module"]
        ntasks = np if np is not None else HPL_CFG["slurm"]["ntasks"]
        cpus   = HPL_CFG["slurm"]["cpus_per_task"]
        time   = HPL_CFG["slurm"]["time"]
        cmd    = hpl.get_build_cmd(compiler) if kind == "build" else hpl.get_run_cmd(compiler, threads, np)
        binary = HPL_CFG["binaries"].get(compiler, HPL_CFG["binaries"]["intel"])

    lines = []
    lines.append("#!/bin/bash")
    lines.append(f"#SBATCH --job-name={app}_{kind}")
    lines.append(f"#SBATCH --partition={CFG['cluster']['partition']}")
    lines.append(f"#SBATCH --nodes={CFG['cluster']['nodes']}")
    lines.append(f"#SBATCH --ntasks={ntasks}")
    lines.append(f"#SBATCH --cpus-per-task={cpus}")
    lines.append(f"#SBATCH --time={time}")
    lines.append(f"#SBATCH --output={out}")
    lines.append(f"#SBATCH --error={err}")
    lines.append(f"mkdir -p {os.path.join(results_dir, '$SLURM_JOB_ID')}")
    lines.append("")
    lines.append(f"module load {module}")
    if app == "hpl" and compiler == "aocc":
        lines.append("module load aocl/4.2")
    lines.append("")
    lines.append('echo "Job started at $(date) on $(hostname)"')
    lines.append("")

    if kind == "build":
        # ensure source is present before compiling
        if app == "stream":
            lines.append(f'python3 -c "import sys; sys.path.insert(0,\'{BASE_DIR}\'); from benchmarks import stream; stream.ensure_source()"')
        else:
            lines.append(f'python3 -c "import sys; sys.path.insert(0,\'{BASE_DIR}\'); from benchmarks import hpl; hpl.ensure_source(\'{compiler}\')"')
        lines.append("")
        lines.append("# compile")

    lines.append(cmd)
    lines.append("")

    if kind == "build":
        # verify binary was created
        lines.append(f'if [ ! -x "{binary}" ]; then')
        lines.append('    echo "Build failed - binary not found"')
        lines.append("    exit 1")
        lines.append("fi")
        lines.append(f'echo "Build successful: {binary}"')
        lines.append("")

    lines.append('echo "Job finished at $(date)"')

    script = "\n".join(lines) + "\n"

    scripts_dir = os.path.join(BASE_DIR, "scripts")
    path = os.path.join(scripts_dir, f"run_{app}_{kind}.sbatch")

    with open(path, "w") as f:
        f.write(script)

    # make it executable
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    print(f"Generated: scripts/run_{app}_{kind}.sbatch")
    return path
