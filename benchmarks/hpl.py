import os
import sys
import subprocess
import tarfile
from config import HPL_CFG

def check_binary(compiler):
    binary = HPL_CFG["binaries"].get(compiler, HPL_CFG["binaries"]["intel"])
    if os.path.isfile(binary) and os.access(binary, os.X_OK):
        return True
    print(f"[hpl] binary not found at {binary}")
    print("[hpl] will build from source")
    return False

def ensure_source(compiler):
    hpl_dir = HPL_CFG["dir"]
    url     = HPL_CFG["src_url"]
    tarball = HPL_CFG["src_tarball"]

    # check if source tree is present, download if not
    if not os.path.isdir(hpl_dir):
        print(f"[hpl] source not found at {hpl_dir}")
        print(f"[hpl] downloading from {HPL_CFG['src_url']}")
        ret = subprocess.run(["wget", "-q", "-O", tarball, HPL_CFG["src_url"]])
        if ret.returncode != 0:
            print("[hpl] download failed")
            sys.exit(1)
        print("[hpl] extracting...")
        with tarfile.open(tarball) as tar:
            tar.extractall(path=os.path.expanduser("~"))
        os.remove(tarball)
        print(f"[hpl] source ready at {hpl_dir}")
    else:
        print(f"[hpl] source found at {hpl_dir}")

    # check makefile exists for chosen compiler
    makefile = HPL_CFG["makefiles"].get(compiler)
    if not makefile or not os.path.isfile(makefile):
        print(f"[hpl] Make.{compiler} not found at {makefile}")
        sys.exit(1)
    print(f"[hpl] makefile found: {makefile}")

    # check mpi directory
    tarball = HPL_CFG["src_tarball"] 
    comp    = HPL_CFG["compilers"][compiler]
    mpi_dir = comp["mpi_dir"]
    if not os.path.isdir(mpi_dir):
        print(f"[hpl] MPI directory not found: {mpi_dir}")
        print(f"[hpl] run: module load {comp['module']}")
        sys.exit(1)
    print(f"[hpl] MPI found at {mpi_dir}")

    # check blas directory
    blas_dir = comp["blas_dir"]
    if not os.path.isdir(blas_dir):
        print(f"[hpl] BLAS directory not found: {blas_dir}")
        print(f"[hpl] run: module load {comp['module']}")
        sys.exit(1)
    print(f"[hpl] BLAS found at {blas_dir}")

    # patch makefile with correct paths from yaml
    from scripts.patch_makefile import patch_makefile
    patch_makefile(compiler)

def get_build_cmd(compiler):
    src_dir = HPL_CFG["src_dir"]
    return f"cd {src_dir} && make arch={compiler} -j$(nproc)"

def get_run_cmd(compiler, threads=None, np=None): 
    comp   = HPL_CFG["compilers"][compiler] 
    binary = HPL_CFG["binaries"].get(compiler, HPL_CFG["binaries"]["intel"])
    bindir = os.path.dirname(binary) 
    mpirun = comp["mpi_run"] 
    iterations  = HPL_CFG["iterations"]
    thread_list = [threads] if threads is not None else HPL_CFG["threads"]



    lines = []
    for t in thread_list:
        for i in range(1, iterations + 1):
            lines.append(f"echo \"--- threads={t} iteration={i} ---\"")
            lines.append(f"export OMP_NUM_THREADS={t}")
            lines.append(f"cd {bindir}")
            lines.append(f"{mpirun} -np $SLURM_NTASKS {binary}")
    return "\n".join(lines)
