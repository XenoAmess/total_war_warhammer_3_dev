"""Invoke the selected Mod's own preview renderer."""
import argparse
import subprocess
import sys
from pathlib import Path

from project import ROOT, add_mod_argument, selected_project


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    add_mod_argument(parser)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    project = selected_project(parser, args.mod)
    renderer = project.root / 'tools/preview.py'
    if not renderer.is_file():
        parser.error(f'Mod {project.id!r} has no preview renderer')
    output = (args.output or project.build_dir / 'preview.png').resolve()
    subprocess.run([sys.executable, str(renderer), '--output', str(output)], cwd=ROOT, check=True)
