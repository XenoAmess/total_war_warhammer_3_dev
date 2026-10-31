"""Run shared tool tests and the explicitly selected Mod's offline suite."""
import argparse
import subprocess
import sys

from project import ROOT, add_mod_argument, selected_project


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    add_mod_argument(parser)
    args = parser.parse_args()
    project = selected_project(parser, args.mod)
    runner = project.root / 'tests/run.py'
    if not runner.is_file():
        parser.error(f'Mod {project.id!r} has no offline test runner')
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py'],
                   cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(runner)], cwd=ROOT, check=True)
