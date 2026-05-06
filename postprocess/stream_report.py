import os
import re


def parse_stream_log(log_path):
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

        metrics = {}
        for kernel in ["Copy", "Scale", "Add", "Triad"]:
            match = re.search(rf"{kernel}:\s+([\d.]+)", section_text)
            if match:
                metrics[kernel] = float(match.group(1))

        if metrics:
            results.append({
                "threads":   thread_count,
                "iteration": iteration,
                "metrics":   metrics,
                "passed":    "Solution Validates" in section_text,
            })
        i += 3

    success = any(r["passed"] for r in results)
    return success, results

def parse_all_logs(results_dir):
    thread_data = {}

    if not os.path.isdir(results_dir):
        return thread_data

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

            if thread_count not in thread_data:
                thread_data[thread_count] = {"Copy": [], "Scale": [], "Add": [], "Triad": []}

            for kernel in ["Copy", "Scale", "Add", "Triad"]:
                match = re.search(rf"{kernel}:\s+([\d.]+)", section_text)
                if match:
                    thread_data[thread_count][kernel].append(float(match.group(1)))

            i += 2

    return thread_data

def print_averages(results_dir):
    """
    Print average bandwidth per kernel for each thread count.
    """
    thread_data = parse_all_logs(results_dir)

    if not thread_data:
        print("  No STREAM results found in:", results_dir)
        return

    print()
    print(f"  STREAM Average Bandwidth (MB/s) by Thread Count")
    print(f"  {'─'*65}")
    print(f"  {'Threads':<12} {'Iterations':<12} {'Copy':<14} {'Scale':<14} {'Add':<14} {'Triad'}")
    print(f"  {'─'*65}")

    for threads in sorted(thread_data.keys()):
        kernels = thread_data[threads]
        iters = len(kernels["Copy"])
        avg = {k: sum(v)/len(v) for k, v in kernels.items() if v}
        print(f"  {threads:<12} {iters:<12} {avg.get('Copy',0):<14.2f} {avg.get('Scale',0):<14.2f} {avg.get('Add',0):<14.2f} {avg.get('Triad',0):.2f}")

    print(f"  {'─'*65}")
    print()

def save_table(job_id, threads, kind, log_path, job_dir, binary_status="Built now"):
    success, results = parse_stream_log(log_path)
    build_status = "✔ SUCCESS" if success else "✘ FAILED"

    lines = []
    lines.append(f"{'='*55}")
    lines.append(f"  STREAM Job Report")
    lines.append(f"{'='*55}")
    lines.append(f"  Job ID         : {job_id}")
    lines.append(f"  Threads        : {threads}")
    lines.append(f"  Phase          : {kind}")
    lines.append(f"  Binary Status  : {binary_status}")
    lines.append(f"  Build Status   : {build_status}")
    lines.append(f"  Log            : {log_path}")
    lines.append(f"{'─'*55}")
    if kind == "run" and results:
        for r in results:
            lines.append(f"  Iteration {r['iteration']} (threads={r['threads']})")
            lines.append(f"  {'Kernel':<10} {'Bandwidth (MB/s)':>20}")
            lines.append(f"  {'─'*32}")
            for k, v in r["metrics"].items():
                val = f"{v:.2f}" if v is not None else "N/A"
                lines.append(f"  {k:<10} {val:>20}")
            lines.append(f"  {'─'*32}")
    elif not success:
        lines.append("  ✘ No results found — job may have failed")
        lines.append(f"  Check log : {log_path}")
    lines.append(f"{'='*55}")

    os.makedirs(job_dir, exist_ok=True)
    report_path = os.path.join(job_dir, "stream.out")
    with open(report_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    # rest of print box unchanged ...


    # ── print clean summary to screen ──────────────────────── #
    w = 45
    print(f"\n  ┌{'─'*w}┐")
    print(f"  │{'STREAM Post Process Report':^{w}}│")
    print(f"  ├{'─'*20}┬{'─'*(w-21)}┐")
    print(f"  │ {'Job ID':<18} │ {str(job_id):<{w-22}} │")
    print(f"  │ {'Threads':<18} │ {str(threads):<{w-22}} │")
    print(f"  │ {'Phase':<18} │ {kind:<{w-22}} │")
    print(f"  │ {'Binary Status':<18} │ {binary_status:<{w-22}} │")
    print(f"  │ {'Build Status':<18} │ {build_status:<{w-22}} │")
    print(f"  └{'─'*20}┴{'─'*(w-21)}┘")
    print()
    stream_results_dir = os.path.join(os.path.dirname(job_dir), "")
    print_averages(job_dir)
    return report_path
