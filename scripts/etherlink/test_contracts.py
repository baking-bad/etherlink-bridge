import click
import subprocess


@click.command()
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
