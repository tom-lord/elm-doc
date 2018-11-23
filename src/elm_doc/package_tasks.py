from typing import List, Optional
import os
import os.path
from pathlib import Path
import shutil
import urllib.error
import urllib.request

from doit.tools import create_folder
from retrying import retry

from elm_doc import page_template
from elm_doc.elm_project import ElmPackage, ModuleName


def build_package_page(output_path: Path, mount_point: str = ''):
    os.makedirs(os.path.dirname(str(output_path)), exist_ok=True)
    with open(str(output_path), 'w') as f:
        f.write(page_template.render(mount_point=mount_point))


def link_latest_package_dir(package_dir: Path, link_path: Path):
    os.makedirs(str(package_dir), exist_ok=True)
    # prefer relative path to make the built documentation directory relocatable
    link_path.symlink_to(package_dir.relative_to(link_path.parent), target_is_directory=True)


def copy_package_readme(package_readme: Path, output_path: Path):
    if package_readme.is_file():
        shutil.copy(str(package_readme), str(output_path))


@retry(
    retry_on_exception=lambda e: isinstance(e, urllib.error.URLError),
    wait_exponential_multiplier=1000,  # Wait 2^x * 1000 milliseconds between each retry,
    wait_exponential_max=30 * 1000,  # up to 30 seconds, then 30 seconds afterwards
    stop_max_attempt_number=10)
def download_package_docs_json(package: ElmPackage, output_path: Path):
    url = 'https://package.elm-lang.org/packages/{name}/{version}/docs.json'.format(
        name=package.name, version=package.version
    )
    urllib.request.urlretrieve(url, str(output_path))


def _package_task_basename_factory(package):
    return lambda name: '{}:{}/{}'.format(name, package.name, package.version)


def create_dependency_tasks(
        output_path: Optional[Path],
        package: ElmPackage,
        mount_point: str = ''):
    basename = _package_task_basename_factory(package)
    package_modules = package.exposed_modules
    package_output_path = package_docs_root(output_path, package)

    # package documentation.json
    docs_json_path = package_output_path / 'documentation.json'
    yield {
        'basename': basename('download_package_docs_json'),
        'actions': [(create_folder, (str(package_output_path),)),
                    (download_package_docs_json, (package, docs_json_path))],
        'targets': [docs_json_path],
        # 'file_dep': [all_elm_files_in_source_dirs] # todo
        'uptodate': [True],
    }

    for page_task in create_package_page_tasks(output_path, package, package_modules, mount_point):
        yield page_task


def create_package_page_tasks(
        output_path: Optional[Path],
        package: ElmPackage,
        package_modules: List[ModuleName],
        mount_point: str = '',):
    basename = _package_task_basename_factory(package)
    package_output_path = package_docs_root(output_path, package)

    # package index page
    package_index_output = package_output_path / 'index.html'
    yield {
        'basename': basename('package_page'),
        'actions': [(build_package_page, (package_index_output,), {'mount_point': mount_point})],
        'targets': [package_index_output],
        # 'file_dep': [module['source_file']] #todo
        'uptodate': [True],
    }

    # package readme
    readme_filename = 'README.md'
    package_readme = package.path / readme_filename
    output_readme_path = package_output_path / readme_filename
    if package_readme.is_file():
        yield {
            'basename': basename('package_readme'),
            'actions': [(copy_package_readme, (package_readme, output_readme_path))],
            'targets': [output_readme_path],
            'file_dep': [package_readme],
        }

    # link from /latest
    latest_path = package_output_path.parent / 'latest'
    yield {
        'basename': basename('package_latest_link'),
        'actions': [(link_latest_package_dir, (package_output_path, latest_path))],
        'targets': [latest_path],
        # 'file_dep': [], # todo
        'uptodate': [True]
    }

    # module pages
    for module in package_modules:
        module_output = package_output_path / module.replace('.', '-')
        yield {
            'basename': basename('module_page') + ':' + module,
            'actions': [(build_package_page, (module_output,), {'mount_point': mount_point})],
            'targets': [module_output],
            # 'file_dep': [module['source_file']] #todo
            'uptodate': [True],
        }


def package_docs_root(output_path: Optional[Path], package: ElmPackage) -> Path:
    return output_path / 'packages' / package.user / package.project / package.version
