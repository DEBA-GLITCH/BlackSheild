# scripts/run.py
#
# BlackSheild CLI entrypoint.
#
# Usage:
#   python scripts/run.py --target requests --type package --ecosystem PyPI
#   python scripts/run.py --target example.com --type domain
#   python scripts/run.py --target pallets --type org

import argparse
import sys
import uuid
from pathlib import Path

# Add project root to path so we can import blacksheild without pip install
sys.path.insert(0, str(Path(__file__).parent.parent))

from blacksheild.core.state import TargetInput, initial_state
from blacksheild.graph.builder import build_graph


VALID_TYPES      = {"domain", "package", "org"}
VALID_ECOSYSTEMS = {"PyPI", "npm", "Go", "Maven", "RubyGems", "NuGet", "Cargo", "Hex"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BlackSheild - Threat Intelligence Orchestrator")
    parser.add_argument("--target", required=True,
                        help="Target to analyze: domain name, package name, or org name")
    parser.add_argument("--type", required=True, choices=list(VALID_TYPES), dest="target_type",
                        help="Type of target")
    parser.add_argument("--ecosystem", default=None,
                        help="Package ecosystem, required when --type is package")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Fail fast with a clear message before building the graph."""
    if args.target_type == "package" and not args.ecosystem:
        print(
            f"ERROR: --ecosystem is required when --type is package\n"
            f"Valid ecosystems: {', '.join(sorted(VALID_ECOSYSTEMS))}",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.ecosystem and args.ecosystem not in VALID_ECOSYSTEMS:
        print(
            f"ERROR: Unknown ecosystem '{args.ecosystem}'\n"
            f"Valid ecosystems: {', '.join(sorted(VALID_ECOSYSTEMS))}",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    args = parse_args()
    validate_args(args)

    # Build and compile the graph once per process
    graph = build_graph()

    correlation_id = f"bs-{uuid.uuid4()}"
    target: TargetInput = {
        "type": args.target_type,
        "value": args.target.strip().lower(),
        "ecosystem": args.ecosystem,
    }

    state = initial_state(correlation_id, target)

    print(f"Starting BlackSheild analysis")
    print(f"  Correlation ID : {correlation_id}")
    print(f"  Target         : {target['value']} ({target['type']})")
    if target["ecosystem"]:
        print(f"  Ecosystem      : {target['ecosystem']}")
    print()

    # Invoke the graph synchronously
    # Phase 1: all stub nodes, returns minimal output
    # Phase 3+: real nodes, writes full JSON report to disk
    result = graph.invoke(state)

    if result.get("report_path"):
        print(f"Report written to: {result['report_path']}")
    else:
        print("Run complete (Phase 1 stub run - no report produced yet)")

    if result.get("errors"):
        print(f"\nErrors ({len(result['errors'])}):")
        for err in result["errors"]:
            print(f"  [{err.get('node', 'unknown')}] {err.get('message', 'no message')}")


if __name__ == "__main__":
    main()