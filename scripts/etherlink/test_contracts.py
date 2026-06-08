import subprocess

from scripts import cli_options


def test_contracts() -> None:
    """Runs tests for contracts"""

    print('Testing Etherlink side contracts:')
    result = subprocess.run(
        ['forge', 'test'],
        cwd='etherlink',
        check=True,
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    print('Done')


test_contracts_command = cli_options.command(
    test_contracts,
    name='etherlink_tests',
    options=[],
)
