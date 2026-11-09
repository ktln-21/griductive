"""
Benchmark and Experiments Script for Griductive Solver (CSC14003 - Project 2).
Automates performance evaluations across 3x3, 4x4, and 5x5 (stress test) levels.
Collects the 6 required metric categories:
1. Primary and Auxiliary variables
2. CNF clauses
3. Total SAT solver calls
4. Decisions, Propagations, Backtracks
5. Deduction steps and Reveal waves
6. Total runtime in milliseconds

Outputs:
- benchmark/experiment_results.csv
- benchmark/experiment_summary.md (Markdown report table)
- benchmark/experiment_table.tex (LaTeX table for PDF report)
- benchmark/plots/ (High-res PNG charts for the report)
"""
import csv
import json
import os
import sys
import time
from typing import Any, Dict, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.engine import GameEngine
from solver.agent import DeductiveLogicAgent
from solver.cnf_encoder import CNFEncoder


def run_all_benchmarks(
    manifest_path: str = os.path.join(PROJECT_ROOT, "levels", "levels_manifest.json"),
    output_dir: str = os.path.join(PROJECT_ROOT, "benchmark")
) -> List[Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        levels = json.load(f)

    print(f"Loaded {len(levels)} levels for benchmarking...")
    results = []

    for idx, lvl in enumerate(levels):
        lvl_id = lvl["id"]
        lvl_name = lvl["name"]
        chapter = lvl["chapter"]
        size = lvl["size"]

        engine = GameEngine(size)
        engine.load_level(lvl)

        agent = DeductiveLogicAgent()
        encoder = CNFEncoder(size)
        pub_initial = engine.get_public_state()
        init_kb = encoder.build_kb(pub_initial)

        start_time = time.perf_counter()
        solved = agent.auto_solve(engine)
        total_time_ms = (time.perf_counter() - start_time) * 1000.0

        pub_final = engine.get_public_state()
        final_kb = encoder.build_kb(pub_final)

        steps_count = len(agent.deduction_trace)
        decisions = agent.cumulative_metrics.decisions
        propagations = agent.cumulative_metrics.propagations
        backtracks = agent.cumulative_metrics.backtracks
        sat_calls = agent.total_sat_calls

        row = {
            "level_id": lvl_id,
            "level_name": lvl_name,
            "chapter": chapter,
            "grid_size": f"{size}x{size}",
            "size_n": size,
            "primary_vars": size * size,
            "aux_vars": encoder.aux_var_count,
            "cnf_clauses_initial": len(init_kb),
            "cnf_clauses_final": len(final_kb),
            "sat_calls": sat_calls,
            "decisions": decisions,
            "propagations": propagations,
            "backtracks": backtracks,
            "deduction_steps": steps_count,
            "runtime_ms": round(total_time_ms, 2),
            "solved_100_pct": solved and engine.is_solved(),
        }
        results.append(row)
        print(f"[{idx + 1:02d}/{len(levels)}] {lvl_name} -> Solved: {row['solved_100_pct']}, SAT Calls: {sat_calls}, Time: {row['runtime_ms']}ms")

    # 1. Export CSV
    csv_path = os.path.join(output_dir, "experiment_results.csv")
    fieldnames = list(results[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"Exported CSV: {csv_path}")

    # 2. Aggregations by Grid Size & Chapter
    sizes = sorted(list(set(r["size_n"] for r in results)))
    summary_by_size = {}
    for s in sizes:
        subset = [r for r in results if r["size_n"] == s]
        n_sub = len(subset)
        summary_by_size[s] = {
            "count": n_sub,
            "avg_clauses": sum(r["cnf_clauses_final"] for r in subset) / n_sub,
            "avg_sat_calls": sum(r["sat_calls"] for r in subset) / n_sub,
            "avg_decisions": sum(r["decisions"] for r in subset) / n_sub,
            "avg_propagations": sum(r["propagations"] for r in subset) / n_sub,
            "avg_backtracks": sum(r["backtracks"] for r in subset) / n_sub,
            "avg_runtime_ms": sum(r["runtime_ms"] for r in subset) / n_sub,
            "success_rate": (sum(1 for r in subset if r["solved_100_pct"]) / n_sub) * 100.0,
        }

    # 3. Export Markdown Report Table
    md_path = os.path.join(output_dir, "experiment_summary.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Griductive Solver Experimental Evaluation\n\n")
        f.write("## Summary Metrics by Board Dimension\n\n")
        f.write("| Grid Size | Levels | Avg CNF Clauses | Avg SAT Calls | Avg Decisions | Avg Propagations | Avg Backtracks | Avg Runtime (ms) | Success Rate |\n")
        f.write("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for s, stats in summary_by_size.items():
            f.write(
                f"| {s}x{s} | {stats['count']} | {stats['avg_clauses']:.1f} | "
                f"{stats['avg_sat_calls']:.1f} | {stats['avg_decisions']:.1f} | "
                f"{stats['avg_propagations']:.1f} | {stats['avg_backtracks']:.1f} | "
                f"{stats['avg_runtime_ms']:.2f}ms | {stats['success_rate']:.1f}% |\n"
            )
        f.write("\n\n## Complete Level Benchmark Dataset\n\n")
        f.write("| Level ID | Case Name | Grid | CNF Clauses | SAT Calls | Decisions | Propagations | Backtracks | Runtime (ms) |\n")
        f.write("|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
        for r in results:
            f.write(
                f"| {r['level_id']} | {r['level_name']} | {r['grid_size']} | "
                f"{r['cnf_clauses_final']} | {r['sat_calls']} | {r['decisions']} | "
                f"{r['propagations']} | {r['backtracks']} | {r['runtime_ms']} |\n"
            )
    print(f"Exported Markdown: {md_path}")

    # 4. Export LaTeX Table for PDF report
    tex_path = os.path.join(output_dir, "experiment_table.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% Auto-generated LaTeX table for CSC14003 Project 2 Report\n")
        f.write("\\begin{table}[htbp]\n")
        f.write("\\centering\n")
        f.write("\\caption{DPLL and CNF Performance Across Griductive Board Dimensions}\n")
        f.write("\\label{tab:dpll_experiments}\n")
        f.write("\\begin{tabular}{lcccccccc}\n")
        f.write("\\hline\n")
        f.write("Grid & $N_{\\text{levels}}$ & Clauses & SAT Calls & Decisions & Propagations & Backtracks & Time (ms) & Solved \\\\\n")
        f.write("\\hline\n")
        for s, stats in summary_by_size.items():
            f.write(
                f"{s}$\\times${s} & {stats['count']} & {stats['avg_clauses']:.1f} & "
                f"{stats['avg_sat_calls']:.1f} & {stats['avg_decisions']:.1f} & "
                f"{stats['avg_propagations']:.1f} & {stats['avg_backtracks']:.1f} & "
                f"{stats['avg_runtime_ms']:.2f} & {stats['success_rate']:.0f}\\% \\\\\n"
            )
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")
    print(f"Exported LaTeX: {tex_path}")

    # 5. Generate Matplotlib Charts
    generate_plots(summary_by_size, results, plots_dir)

    return results


def generate_plots(summary_by_size: Dict[int, Any], results: List[Dict[str, Any]], plots_dir: str) -> None:
    # Plot 1: Runtime by Grid Size
    sizes = sorted(list(summary_by_size.keys()))
    avg_times = [summary_by_size[s]["avg_runtime_ms"] for s in sizes]
    size_labels = [f"{s}x{s}" for s in sizes]

    plt.figure(figsize=(7, 4.5))
    bars = plt.bar(size_labels, avg_times, color=["#38b764", "#29adff", "#ef7d57"], edgecolor="black", linewidth=1.5)
    plt.title("Average Deductive Solving Runtime by Grid Dimension", fontsize=12, fontweight="bold")
    plt.xlabel("Grid Dimension (NxN)", fontsize=10)
    plt.ylabel("Execution Time (milliseconds)", fontsize=10)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f} ms", ha="center", va="bottom", fontsize=9, fontweight="bold")
    plt.tight_layout()
    p1 = os.path.join(plots_dir, "runtime_by_grid_size.png")
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"Saved plot: {p1}")

    # Plot 2: DPLL Operations Breakdown (Propagations, Decisions, Backtracks)
    props = [summary_by_size[s]["avg_propagations"] for s in sizes]
    decs = [summary_by_size[s]["avg_decisions"] for s in sizes]
    backs = [summary_by_size[s]["avg_backtracks"] for s in sizes]

    x = range(len(sizes))
    width = 0.25

    plt.figure(figsize=(8, 4.8))
    plt.bar([p - width for p in x], props, width=width, label="Unit Propagations", color="#38b764", edgecolor="black")
    plt.bar(x, decs, width=width, label="Decisions (Branching)", color="#29adff", edgecolor="black")
    plt.bar([p + width for p in x], backs, width=width, label="Backtracks (Conflicts)", color="#e43b44", edgecolor="black")
    plt.xticks(x, size_labels, fontsize=10)
    plt.title("DPLL Solver Operations Breakdown by Grid Dimension", fontsize=12, fontweight="bold")
    plt.xlabel("Grid Dimension (NxN)", fontsize=10)
    plt.ylabel("Average Count per Level", fontsize=10)
    plt.legend(frameon=True)
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    p2 = os.path.join(plots_dir, "dpll_metrics_comparison.png")
    plt.savefig(p2, dpi=300)
    plt.close()
    print(f"Saved plot: {p2}")

    # Plot 3: Clauses vs SAT Calls Scatter/Distribution
    plt.figure(figsize=(7.5, 4.5))
    colors = {3: "#38b764", 4: "#29adff", 5: "#ef7d57"}
    for s in sizes:
        subset = [r for r in results if r["size_n"] == s]
        plt.scatter(
            [r["cnf_clauses_final"] for r in subset],
            [r["sat_calls"] for r in subset],
            c=colors.get(s, "blue"),
            label=f"{s}x{s} Grid",
            edgecolors="black",
            s=60,
            alpha=0.85
        )
    plt.title("CNF Clauses vs. Total SAT Solver Calls", fontsize=12, fontweight="bold")
    plt.xlabel("Number of CNF Clauses in Final KB", fontsize=10)
    plt.ylabel("Total SAT Solver Calls", fontsize=10)
    plt.legend(frameon=True)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    p3 = os.path.join(plots_dir, "clauses_and_sat_calls.png")
    plt.savefig(p3, dpi=300)
    plt.close()
    print(f"Saved plot: {p3}")


if __name__ == "__main__":
    run_all_benchmarks()
