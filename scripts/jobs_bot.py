"""Jobs bot. All the logic lives in core/; this file only starts it."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.runner import run_niche  # noqa: E402

if __name__ == "__main__":
    sys.exit(run_niche("jobs"))