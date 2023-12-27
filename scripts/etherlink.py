import click
from dotenv import load_dotenv
from getpass import getpass
import subprocess
from typing import Optional
from scripts.environment import load_or_ask


@click.command()
@click.option('--private-key', default=None, help='Use the provided private key')
@click.option('--rpc-url', default=None, help='Etherlink RPC URL')
def check_script_runs(
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    # TODO: this is test function to check that everything works fine
    private_key = private_key or load_or_ask('L2_PRIVATE_KEY')
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')

    result = subprocess.run(
        [
            'cast',
            'wallet',
            'address',
            '--private-key',
            private_key,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    print(f'L2 public key: {result.stdout.strip()}')
