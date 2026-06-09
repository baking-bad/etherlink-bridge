import subprocess

from scripts import cli_options


def build_contracts() -> None:
    """Compiles contracts"""

    # TODO: consider checking that the user has forge installed
    print('Compiling Etherlink side contracts:')
    result = subprocess.run(
        ['forge', 'build'],
        cwd='etherlink',
        check=True,
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    print('Done')


build_contracts_command = cli_options.command(
    build_contracts,
    name='build_etherlink_contracts',
    options=[],
)
