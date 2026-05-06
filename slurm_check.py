import os
import shutil
import subprocess
import sys

SLURM_BINARIES = ["sbatch", "squeue", "sacct", "sinfo", "scontrol"]

def check_slurm():
    print("Checking SLURM binaries...")
    all_found = True

    for binary in SLURM_BINARIES:
        path = shutil.which(binary)
        if path:
            print(f"  found: {binary} -> {path}")
        else:
            print(f"  missing: {binary}")
            all_found = False

    if all_found:
        print("All SLURM binaries found, skipping build")
        show_sinfo()
        return True
    else:
        print("Some SLURM binaries missing, need to build from source")
        return False

def show_sinfo():
    print("\nCluster info (sinfo):")
    ret = subprocess.run(["sinfo"], capture_output=True, text=True)
    if ret.returncode == 0:
        print(ret.stdout)
    else:
        print("  sinfo failed:", ret.stderr.strip())

def build_slurm():
    print("Building SLURM from source...")

    if not shutil.which("wget"):
        print("wget not found, cannot download slurm source")
        sys.exit(1)

    home = os.path.expanduser("~")
    slurm_version = "23.11.4"
    slurm_tar = f"slurm-{slurm_version}.tar.bz2"
    slurm_url = f"https://download.schedmd.com/slurm/{slurm_tar}"
    slurm_src = os.path.join(home, f"slurm-{slurm_version}")
    install_dir = os.path.join(home, "slurm-install")

    tarball_path = os.path.join(home, slurm_tar)
    if not os.path.isfile(tarball_path):
        print(f"Downloading SLURM {slurm_version}...")
        ret = os.system(f"wget -q -O {tarball_path} {slurm_url}")
        if ret != 0:
            print("Download failed")
            sys.exit(1)
        print("Download done")
    else:
        print(f"Source tarball already exists: {tarball_path}")

    if not os.path.isdir(slurm_src):
        print("Extracting...")
        ret = os.system(f"tar -xjf {tarball_path} -C {home}")
        if ret != 0:
            print("Extraction failed")
            sys.exit(1)
        print("Extraction done")
    else:
        print(f"Source already extracted: {slurm_src}")

    print("Configuring...")
    os.makedirs(install_dir, exist_ok=True)
    ret = os.system(f"cd {slurm_src} && ./configure --prefix={install_dir}")
    if ret != 0:
        print("Configure failed")
        sys.exit(1)

    print("Compiling...")
    ret = os.system(f"cd {slurm_src} && make -j$(nproc)")
    if ret != 0:
        print("Build failed")
        sys.exit(1)

    print("Installing...")
    ret = os.system(f"cd {slurm_src} && make install")
    if ret != 0:
        print("Install failed")
        sys.exit(1)

    print(f"SLURM installed at: {install_dir}")
    print(f"Add to PATH: export PATH={install_dir}/bin:$PATH")

def run():
    found = check_slurm()
    if not found:
        build_slurm()

if __name__ == "__main__":
    run()
