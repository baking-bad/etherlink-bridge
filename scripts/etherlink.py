import click
import subprocess
from typing import Optional
from scripts.environment import load_or_ask


@click.command()
@click.option('--public-key', default=None, help='Etherlink address to fund.')
@click.option(
    '--sender-private-key',
    default=None,
    help='Use the provided private key to fund from.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def fund_account(
    public_key: Optional[str],
    sender_private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Funds given Etherlink address with 1 tez"""

    public_key = public_key or load_or_ask('L2_PUBLIC_KEY')
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    sender_private_key = sender_private_key or load_or_ask('L2_MASTER_KEY')

    result = subprocess.run(
        [
            'cast',
            'send',
            public_key,
            '--value',
            '1ether',
            '--private-key',
            sender_private_key,
            '--rpc-url',
            rpc_url,
            '--legacy',
        ],
        cwd='etherlink',
        check=True,
        capture_output=True,
        text=True,
    )
    print('Successfully funded account:')
    print(result.stdout)


@click.command()
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticketer-content-bytes',
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
    help='The address of the Etherlink kernel which will be managing token.',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def deploy_erc20(
    ticketer_address_bytes: str,
    ticketer_content_bytes: str,
    token_name: str,
    token_symbol: str,
    decimals: int,
    kernel_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Deploys ERC20 Proxy contract with given parameters"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY')
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
            ticketer_content_bytes,
            kernel_address,
            token_name,
            token_symbol,
            '0',
            '--gas-limit',
            '200000',
        ],
        cwd='etherlink',
        # check=True,
        capture_output=True,
        text=True,
    )

    print('Successfully deployed ERC20 contract:')
    print(result.stdout)
