import os
import re


def parse_hpl_log(log_path):
    if not os.path.isfile(log_path):
        return False, []

    with open(log_path) as f:
        content = f.read()

    sections = re.split(r'--- threads=(\d+) iteration=(\d+) ---', content)
    results = []

    i = 1
    while i < len(sections) - 2:
        thread_count = int(sections[i])
        iteration    = int(sections[i + 1])
        section_text = sections[i + 2]

        match = re.search(
            r'WR\S+\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.eE+\-]+)',
            section_text
        )
        if match:
            results.append({
                "threads":   thread_count,
                "iteration": iteration,
                "N":         int(match.group(1)),
                "NB":        int(match.group(2)),
                "P":         int(match.group(3)),
                "Q":         int(match.group(4)),
                "time":      float(match.group(5)),
                "gflops":    float(match.group(6)),
                "passed":    "PASSED" in section_text,
            })
        i += 3

    success = any(r["passed"] for r in results)
    return success, results

def parse_all_logs(results_dir):
    thread_gflops = {}

    if not os.path.isdir(results_dir):
        return thread_gflops

    # Check if run.out is directly in results_dir (single job mode)
    direct_log = os.path.join(results_dir, "run.out")
    if os.path.isfile(direct_log):
        log_files = [direct_log]
    else:
        # Walk subdirectories (historical mode)
        log_files = [
            os.path.join(results_dir, job_id, "run.out")
            for job_id in os.listdir(results_dir)
        ]

    for log_path in log_files:
        if not os.path.isfile(log_path):
            continue

        with open(log_path) as f:
            content = f.read()

        sections = re.split(r'--- threads=(\d+) iteration=\d+ ---', content)
        i = 1
        while i < len(sections) - 1:
            thread_count = int(sections[i])
            section_text = sections[i + 1]

            match = re.search(
                r'WR\S+\s+\d+\s+\d+\s+\d+\s+\d+\s+[\d.]+\s+([\d.eE+\-]+)',
                section_text
            )
            if match:
                gflops = float(match.group(1))
                if thread_count not in thread_gflops:
                    thread_gflops[thread_count] = []
                thread_gflops[thread_count].append(gflops)

            i += 2

    return thread_gflops

def print_averages(results_dir):
    thread_gflops = parse_all_logs(results_dir)

    if not thread_gflops:
        print("  No HPL results found in:", results_dir)
        return

    print()
    print(f"  HPL Average GFLOPS by Thread Count")
    print(f"  {'─'*45}")
    print(f"  {'Threads':<12} {'Iterations':<12} {'Avg GFLOPS':<15} {'Iteration 1':<12} {'Iteration 2'}")
    print(f"  {'─'*45}")

    for threads in sorted(thread_gflops.keys()):
        values = thread_gflops[threads]
        avg    = sum(values) / len(values)
        i1     = min(values)
        i2     = max(values)
        print(f"  {threads:<12} {len(values):<12} {avg:<15.4f} {i1:<12.4f} {i2:.4f}")

    print(f"  {'─'*45}")
    print()

def save_table(job_id, compiler, kind, log_path, job_dir, binary_status="Built now"):
    success, results = parse_hpl_log(log_path)
    build_status = "✔ SUCCESS" if success else "✘ FAILED"

    lines = []
    lines.append(f"{'='*55}")
    lines.append(f"  HPL Result Summary")
    lines.append(f"{'='*55}")
    lines.append(f"  Job ID         : {job_id}")
    lines.append(f"  Compiler       : {compiler.upper()}")
    lines.append(f"  Phase          : {kind}")
    lines.append(f"  Binary Status  : {binary_status}")
    lines.append(f"  Build Status   : {build_status}")
    lines.append(f"  Log            : {log_path}")
    lines.append(f"{'─'*55}")
    if kind == "run" and results:
        for r in results:
            lines.append(f"  Iteration {r['iteration']} (threads={r['threads']})")
            lines.append(f"  {'Metric':<10} {'Value':>15}")
            lines.append(f"  {'─'*27}")
            for k in ["N", "NB", "P", "Q", "time", "gflops"]:
                v = r[k]
                val = f"{v:.4e}" if isinstance(v, float) and v > 1000 else f"{v:.4f}" if isinstance(v, float) else str(v)
                lines.append(f"  {k:<10} {val:>15}")
            status = "✔ PASSED" if r["passed"] else "✘ FAILED"
            lines.append(f"  {'status':<10} {status:>15}")
            lines.append(f"  {'─'*27}")
    elif kind == "build":
        lines.append(f"  Build Status   : {build_status}")
    else:
        lines.append("  ✘ No results found — job may have failed")
        lines.append(f"  Check log : {log_path}")
    lines.append(f"{'='*55}")

    os.makedirs(job_dir, exist_ok=True)
    report_path = os.path.join(job_dir, "hpl.out")
    with open(report_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    # ── print same box format ────────────────────────────────── #
    w = 45
    print(f"\n  ┌{'─'*w}┐")
    print(f"  │{'HPL Post Process Report':^{w}}│")
    print(f"  ├{'─'*20}┬{'─'*(w-21)}┐")
    print(f"  │ {'Job ID':<18} │ {str(job_id):<{w-22}} │")
    print(f"  │ {'Compiler':<18} │ {compiler.upper():<{w-22}} │")
    print(f"  │ {'Phase':<18} │ {kind:<{w-22}} │")
    print(f"  │ {'Binary Status':<18} │ {binary_status:<{w-22}} │")
    print(f"  │ {'Build Status':<18} │ {build_status:<{w-22}} │")
    print(f"  └{'─'*20}┴{'─'*(w-21)}┘")

    return report_path
