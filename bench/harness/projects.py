"""Finds and loads the test projects under bench/projects/."""

import importlib.util

from . import PROJECTS_DIR
from .model import Project


def load_projects() -> dict[str, Project]:
    projects = {}
    for module_path in sorted(PROJECTS_DIR.glob("*/project.py")):
        name = module_path.parent.name
        spec = importlib.util.spec_from_file_location(f"bench_project_{name}", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        project = module.build(module_path.parent)
        projects[project.id] = project
    return projects
