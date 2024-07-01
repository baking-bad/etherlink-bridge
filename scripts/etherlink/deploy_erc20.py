import click
from typing import Optional
import subprocess
from scripts.environment import load_or_ask


@click.command()
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticket-content-bytes',
    required=True,
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. Use `get_ticket_params` function to get the correct value for a given ticket address.',
)
# TODO: consider extracting token name from the ticketer content bytes
@click.option(
    '--token-name', required=True, help='The name of the ERC20 token on Etherlink side.'
)
@click.option(
    '--token-symbol',
    required=True,
    help='The symbol of the ERC20 token on Etherlink side.',
)
@click.option(
    '--decimals',
    default=0,
    help='The number of decimals of the ERC20 token on Etherlink side.',
)
@click.option(
    '--kernel-address',
    default=None,
    help='The address of the Etherlink kernel that will be managing token.',
)
@click.option(
    '--private-key',
    default=None,
    help='Private key that would be used to deploy contract on the Etherlink side.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def deploy_erc20(
    ticketer_address_bytes: str,
    ticket_content_bytes: str,
    token_name: str,
    token_symbol: str,
    decimals: int,
    kernel_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None | str:
    """Deploys ERC20 Proxy contract with given parameters"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    kernel_address = kernel_address or load_or_ask('L2_KERNEL_ADDRESS')

    result = subprocess.run(
        [
            'forge',
            'create',
            '--legacy',
            '--rpc-url',
            rpc_url,
            '--private-key',
            private_key,
            'src/ERC20Proxy.sol:ERC20Proxy',
            '--constructor-args',
            ticketer_address_bytes,
            ticket_content_bytes,
            kernel_address,
            token_name,
            token_symbol,
            str(decimals),
            '--gas-limit',
            '50000000',
            '--gas-price',
            '1000000000',
        ],
        cwd='etherlink',
        # NOTE: not checking for return code, because it is very common
        # to get non-zero exit status
        # check=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stderr)
        return None

    print('Successfully deployed ERC20 contract:')
    print(result.stdout)

    # TODO: consider using more convenient way to get ERC20 address / obj
    #       it would be great to have some kind of ERC20 helper returned
    for line in result.stdout.split('\n'):
        if line.startswith('Deployed to: '):
            return line[15:]
    return None
