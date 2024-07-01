import click
from typing import Optional
import subprocess
from scripts.environment import load_or_ask
from scripts.helpers.utility import make_address_bytes


@click.command()
@click.option(
    '--proxy-address',
    required=True,
    help='The address of the ERC20 proxy token contract which should burn token.',
)
@click.option(
    '--router-address',
    required=True,
    help='The address of the Router contract on the Tezos side (Ticketer address for FA2 and FA1.2 tokens).',
)
@click.option(
    '--amount', required=True, type=int, help='The amount of tokens to be withdrawn.'
)
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
@click.option(
    '--receiver-address',
    default=None,
    help='The address of the receiver of the tokens in Tezos.',
)
@click.option(
    '--withdraw-precompile',
    default=None,
    help='The address of the withdraw precompile contract.',
)
@click.option(
    '--private-key',
    default=None,
    help='Private key on the Etherlink side that should execute withdrawal.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def withdraw(
    proxy_address: str,
    router_address: str,
    amount: int,
    ticketer_address_bytes: str,
    ticket_content_bytes: str,
    receiver_address: Optional[str],
    withdraw_precompile: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Withdraws token from L2 to L1"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    withdraw_precompile = withdraw_precompile or load_or_ask(
        'L2_WITHDRAW_PRECOMPILE_ADDRESS'
    )

    receiver_address = receiver_address or load_or_ask('L1_PUBLIC_KEY_HASH')
    receiver_address_bytes = make_address_bytes(receiver_address)
    router_address_bytes = make_address_bytes(router_address)
    routing_info = receiver_address_bytes + router_address_bytes

    result = subprocess.run(
        [
            'cast',
            'send',
            withdraw_precompile,
            'withdraw(address,bytes,uint256,bytes22,bytes)',
            proxy_address,
            routing_info,
            str(amount),
            ticketer_address_bytes,
            ticket_content_bytes,
            '--rpc-url',
            rpc_url,
            '--private-key',
            private_key,
            '--legacy',
            '--gas-limit',
            '10000000',
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
        return

    print('Successfully called withdraw:')
    print(result.stdout)
