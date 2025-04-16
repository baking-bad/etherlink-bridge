from typing import Optional
import click
import subprocess
import os

from scripts.helpers.formatting import accent, wrap
from scripts.helpers.utility import get_build_dir


@click.command()
@click.option(
    '--ligo-version',
    default='1.3.0',
    help='LIGO compiler version used to compile Tezos side contracts',
    show_default=True,
)
@click.option(
    '--contract-path',
    help='Path to the contract file to compile.',
    required=True,
)
@click.option(
    '--module-name',
    help='Optional name of the contract module to compile.',
    default=None,
)
@click.option(
    '--output-path',
    help='Path to the output compiled `.tz` contract.',
    default=None,
)
def compile_contract(
    ligo_version: str,
    contract_path: str,
    module_name: Optional[str] = None,
    output_path: Optional[str] = None,
) -> None:
    build_dir = get_build_dir()
    if not os.path.exists(build_dir):
        click.echo('Build directory not exist, creating...')
        os.makedirs(build_dir)

    contract_name = os.path.splitext(os.path.basename(contract_path))[0]
    click.echo(' - Compiling ' + wrap(accent(contract_name)) + ' contract')

    if not output_path:
        # NOTE: absolute path is not working here, not sure why:
        # output_path = os.path.join(build_dir, f'{contract_name}.tz')
        output_path = os.path.join('build', f'{contract_name}.tz')

    cwd = os.path.join(os.getcwd(), 'tezos')
    command = [
        'docker',
        'run',
        '--rm',
        '-v',
        f'{cwd}:{cwd}',
        '-w',
        cwd,
        f'ligolang/ligo:{ligo_version}',
        'compile',
        'contract',
        contract_path,
    ]
    if module_name:
        command += ['-m', module_name]
    command += ['-o', output_path]

    result = subprocess.run(
        command,
        cwd=cwd,
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
