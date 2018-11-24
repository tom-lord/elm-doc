'''
'''
from typing import List, Optional
from pathlib import Path

from elm_doc import elm_project
from elm_doc import project_tasks
from elm_doc import package_tasks
from elm_doc import asset_tasks
from elm_doc import catalog_tasks


def build_task_creators(
        project_path: Path,
        project_config: elm_project.ProjectConfig,
        output_path: Optional[Path] = None,
        build_path: Optional[Path] = None,
        elm_path: Optional[Path] = None,
        mount_point: str = '',
        validate: bool = False):
    # todo: gracefully handle missing elm-package.json
    project = elm_project.from_path(project_path)
    if build_path is None:
        build_path = project_path / '.elm-doc'

    task_creators = {}

    task_creators['task_main_project'] = build_main_project_task_creator(
        project,
        project_config,
        output_path,
        build_path,
        elm_path,
        mount_point,
        validate,
    )

    if validate:
        return task_creators

    task_creators['task_dependencies'] = build_dependencies_task_creator(
        project,
        project_config,
        output_path,
        mount_point,
    )
    task_creators['task_assets'] = build_assets_task_creator(output_path)

    return task_creators


def build_main_project_task_creator(
        project: elm_project.ElmProject,
        project_config: elm_project.ProjectConfig,
        output_path: Optional[Path] = None,
        build_path: Optional[Path] = None,
        elm_path: Optional[Path] = None,
        mount_point: str = '',
        validate: bool = False):
    def task_main_project():
        for task in project_tasks.create_main_project_tasks(
                project,
                project_config,
                output_path,
                build_path=build_path,
                elm_path=elm_path,
                mount_point=mount_point,
                validate=validate):
            yield task
    return task_main_project


def build_dependencies_task_creator(
        project: elm_project.ElmProject,
        project_config: elm_project.ProjectConfig,
        output_path: Optional[Path] = None,
        mount_point: str = ''):
    def task_dependencies():
        deps = list(project.iter_dependencies())
        all_packages = [project.as_package(project_config)] + deps

        for package in deps:
            for task in package_tasks.create_dependency_tasks(
                    output_path, package, mount_point):
                yield task

        for task in catalog_tasks.create_catalog_tasks(all_packages, output_path, mount_point=mount_point):
            yield task
    return task_dependencies


def build_assets_task_creator(output_path: Optional[Path] = None):
    def task_assets():
        yield {
            'basename': 'assets',
            'actions': [(asset_tasks.extract_assets, (output_path,))],
            'targets': [output_path / 'assets', output_path / 'artifacts'],
            'file_dep': [asset_tasks.tarball]
        }
    return task_assets
