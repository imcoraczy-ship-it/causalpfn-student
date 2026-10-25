"""Exactly 40 pilot predictions, isolated from formal mechanism IDs.

Monitor the child process using Windows APIs; no extra predictions for warmup.
No automatic retry, seed change, or selective rerun is implemented.
"""
import argparse
import csv
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.e1_5_star_resources import cpu_seconds, memory_trend, memory_usage, physical_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("This resource monitor requires Windows")
    if args.output.exists():
        parser.error("Output directory already exists; choose a new directory")
    system_memory = physical_memory()
    command = [sys.executable, "-B", str(ROOT / "scripts/e1_5_star.py"), "--output", str(args.output),
               "--mechanism-ids", *map(str, range(900, 904)), "--repeat-ids", *map(str, range(5)),
               "--seed", "20261024", "--purpose", "timing_pilot"]
    started = time.perf_counter()
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    samples, measurement_errors = [], []
    # Each sample contains native high-water working set, plus a 20 ms series.
    while child.poll() is None:
        try:
            samples.append(dict(wall_seconds=time.perf_counter()-started, **memory_usage(child._handle)))
        except OSError as exc:
            if child.poll() is None:
                measurement_errors.append(str(exc))
        time.sleep(.02)
    cpu = cpu_seconds(child._handle)  # Windows retains process CPU totals after exit.
    final_peak_note = "Post-exit memory query succeeded"
    try:
        samples.append(dict(wall_seconds=time.perf_counter()-started, **memory_usage(child._handle)))
    except OSError as exc:
        # Some Windows versions release memory counters at exit. The native
        # high-water samples and per-task probes remain explicitly identified.
        final_peak_note = f"Post-exit counters unavailable ({exc}); maximum observed native high-water mark used"
    stdout, stderr = child.communicate()
    wall = time.perf_counter() - started
    if not args.output.is_dir():
        raise RuntimeError(f"Pilot exited {child.returncode} without output directory: {stderr}")
    (args.output / "stdout.txt").write_text(stdout, encoding="utf-8")
    (args.output / "stderr.txt").write_text(stderr, encoding="utf-8")
    with (args.output / "resource_samples.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("wall_seconds", "peak_working_set_bytes", "working_set_bytes", "private_bytes"))
        writer.writeheader()
        writer.writerows(samples)
    # Always retain the process receipt, including failed runs. Never retry.
    receipt = dict(status="process_failed" if child.returncode else "pending_acceptance", exit_code=child.returncode,
                   command=command, monitor_command=sys.argv, wall_seconds=wall,
                   cpu=cpu, platform=platform.platform(), processor=platform.processor(),
                   logical_cpus=os.cpu_count(), sample_interval_seconds=.02, samples=len(samples),
                   physical_memory_at_start=system_memory,
                   final_peak_note=final_peak_note,
                   measurement_errors=measurement_errors,
                   peak_working_set_bytes=max((s["peak_working_set_bytes"] for s in samples), default=0),
                   peak_note="Maximum native process high-water mark observed by the external monitor and per-task probes.")
    report_path = args.output / "runtime_measurement.json"
    report_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if child.returncode:
        raise RuntimeError(f"Pilot failed; retained evidence in {args.output}: {stderr}")
    if not samples or measurement_errors:
        receipt["status"] = "resource_measurement_failed"
        report_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("Resource monitoring failed; inspect runtime_measurement.json; no retry performed")
    # Independent post-process acceptance. This does not perform PFN inference.
    from scripts.e1_5_star_analysis import validate_run
    try:
        acceptance = validate_run(args.output)
    except Exception as exc:
        receipt["status"] = "acceptance_failed"
        receipt["acceptance_error"] = str(exc)
        report_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        raise
    (args.output / "acceptance_report.json").write_text(json.dumps(acceptance, indent=2) + "\n", encoding="utf-8")
    manifest = json.loads((args.output / "manifest.json").read_text(encoding="utf-8"))
    if len(manifest["tasks"]) != 40 or manifest["purpose"] != "timing_pilot":
        raise ValueError("Pilot protocol/count mismatch")
    tasks = manifest["tasks"]
    receipt["peak_working_set_bytes"] = max(receipt["peak_working_set_bytes"],
                                            max(t["resources"]["peak_working_set_bytes"] for t in tasks))
    receipt["memory_trend"] = memory_trend(tasks)
    inference = [t["inference_seconds"] for t in tasks]
    import statistics
    receipt["inference"] = dict(first_seconds=inference[0], subsequent_count=39,
                                subsequent_mean_seconds=statistics.mean(inference[1:]),
                                subsequent_median_seconds=statistics.median(inference[1:]),
                                subsequent_min_seconds=min(inference[1:]), subsequent_max_seconds=max(inference[1:]))
    generation = manifest["timing"]["mechanism_generation_seconds"]
    pair_times = manifest["timing"]["pair_seconds"]
    validation = manifest["acceptance"]["seconds"]
    fixed = max(0., wall - sum(generation) - sum(pair_times) - validation)
    estimate = fixed + 20*statistics.mean(generation) + 200*statistics.mean(pair_times) + 10*validation
    receipt["estimate_400"] = dict(seconds=estimate, fixed_seconds=fixed,
                                   generation_seconds=20*statistics.mean(generation),
                                   paired_work_seconds=200*statistics.mean(pair_times),
                                   validation_seconds=10*validation,
                                   note="One process; measured fixed overhead + 20 mechanisms + 200 pairs + conservative 10x pilot acceptance. Not a measured 400-task run.")
    receipt["output_bytes_before_monitor_receipt"] = sum(p.stat().st_size for p in args.output.iterdir() if p.is_file() and p != report_path)
    receipt["status"] = "accepted" if receipt["memory_trend"]["status"] != "investigate_growth" else "investigate_memory_growth"
    report_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    if receipt["status"] != "accepted":
        raise SystemExit("Memory growth diagnostic flagged; inspect receipt before any formal experiment")


if __name__ == "__main__":
    main()
