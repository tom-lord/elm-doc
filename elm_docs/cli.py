import click
import os
import os.path
from doit.doit_cmd import DoitMain
from doit.cmd_base import ModuleTaskLoader
from elm_docs.tasks import create_tasks


@click.command()
@click.option('--output', '-o')
@click.option('--exclude', '-x', help='comma separated fnmatch pattern of modules to exclude')
@click.argument('project_path')
def main(output, exclude, project_path):
    """Generate your own Elm package documentation site"""
    def task_build():
        if 'ELM_DOCS_EXTENSION_PATH' in os.environ:
            import elm_docs
            elm_docs.__path__.append(os.path.abspath(os.environ['ELM_DOCS_EXTENSION_PATH']))
        exclude_modules = exclude.split(',') if exclude else []
        return create_tasks(project_path, output, exclude_modules=exclude_modules)
    DoitMain(ModuleTaskLoader(locals())).run(['--verbosity', '2'])


if __name__ == '__main__':
    main()
