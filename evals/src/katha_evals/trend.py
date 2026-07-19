"""Score progression across eval rounds: `uv run python -m katha_evals.trend`."""

import glob
import json
import os

from .scorecard import DIMENSIONS, PASS_THRESHOLD

REPORTS_GLOB = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "eval-*.json")


def main() -> None:
    paths = sorted(glob.glob(REPORTS_GLOB))
    if not paths:
        print("no reports yet")
        return
    reports = [(os.path.basename(p)[5:-5], json.load(open(p))) for p in paths]

    personas = sorted({k for _, r in reports for k in r["personas"]})
    for persona in personas:
        print(f"\n== {persona} ==")
        header = "round".ljust(16) + "".join(d[:12].ljust(14) for d in DIMENSIONS) + "gate"
        print(header)
        for stamp, report in reports:
            data = report["personas"].get(persona)
            if not data:
                continue
            row = stamp.ljust(16)
            for dim in DIMENSIONS:
                s = data["scores"].get(dim)
                if s is None:
                    row += "-".ljust(14)
                else:
                    mark = "" if s["score"] >= PASS_THRESHOLD else "*"
                    row += f"{s['score']:.1f}{mark}".ljust(14)
            row += "PASS" if data["passed"] else "FAIL"
            print(row)
    print("\n(* below the 3.5 floor)")


if __name__ == "__main__":
    main()
