#!/usr/bin/env python3
"""
Wrapper utility that runs the sector news agent pipeline against the FinBERT RAG API.

Usage:
    python scripts/run_sector_agents.py [--provider openai] [--skip-rag] [--output-report PATH]

The script automatically:
  * adds agents/sector_news_analysis/src to PYTHONPATH
  * points the agents to the FinBERT RAG API via FINBERT_RAG_BASE_URL
  * executes the upstream run_rag_pipeline.py entry point
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def build_env(agent_src: Path) -> dict[str, str]:
    """Prepare environment variables for the agent pipeline."""
    env = os.environ.copy()

    existing_pythonpath = env.get("PYTHONPATH", "")
    agent_path = str(agent_src)
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{agent_path}{os.pathsep}{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = agent_path

    # Default the FinBERT base URL to local API if the caller did not provide one.
    env.setdefault("FINBERT_RAG_BASE_URL", "http://localhost:8000")

    return env


def run_pipeline(args: argparse.Namespace) -> int:
    """Invoke the upstream run_rag_pipeline.py with the provided arguments."""
    project_root = Path(__file__).resolve().parents[1]
    agent_dir = project_root / "agents" / "sector_news_analysis"
    script_path = agent_dir / "scripts" / "run_rag_pipeline.py"

    if not script_path.exists():
        raise FileNotFoundError(f"Agent pipeline script not found at {script_path}")

    cmd = [
        sys.executable,
        str(script_path),
        "--provider",
        args.provider,
        "--output-report",
        str(args.output_report),
    ]

    if args.skip_rag:
        cmd.append("--skip-rag")

    env = build_env(agent_dir / "src")

    print("🚀 Launching sector agent pipeline")
    print("  Script :", script_path)
    print("  Provider :", args.provider)
    print("  Output report :", args.output_report)
    if args.skip_rag:
        print("  Mode : using bundled sample data")
    print("  FINBERT_RAG_BASE_URL :", env.get("FINBERT_RAG_BASE_URL"))

    result = subprocess.run(cmd, env=env, check=False)
    return result.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sector analysis agents against the FinBERT RAG API")
    parser.add_argument("--provider", default="mock", choices=["mock", "openai"], help="LLM provider for Agent-1")
    parser.add_argument("--skip-rag", action="store_true", help="Use bundled sample data instead of calling the API")
    parser.add_argument(
        "--output-report",
        default=Path("agents/sector_news_analysis/reports/rag_sector_analysis_report.html"),
        type=Path,
        help="Path for the generated HTML report",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exit_code = run_pipeline(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
