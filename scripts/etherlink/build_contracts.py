import click
import subprocess


@click.command()
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
