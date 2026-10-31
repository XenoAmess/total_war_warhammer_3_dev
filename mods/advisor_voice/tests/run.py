"""Run advisor resource research tests without requiring game files."""
import argparse
from pathlib import Path
import sys
import unittest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', required=True, choices=['advisor_voice'])
    parser.parse_args()
    directory = Path(__file__).resolve().parent
    sys.path.insert(0, str(directory.parent / 'tools'))
    suite = unittest.defaultTestLoader.discover(str(directory), pattern='test_*.py')
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
