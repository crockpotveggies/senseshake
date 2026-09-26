"""Repository entry point; uses the descriptor produced by the software checks."""
from pathlib import Path
import sys

SW = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SW / "interfaces/python"), str(SW / "pi")]
from groundlark.cli import main

if __name__ == "__main__": main()
