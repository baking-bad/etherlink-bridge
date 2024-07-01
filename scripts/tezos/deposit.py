import click
from typing import Optional
from scripts.environment import load_or_ask
from scripts.helpers.contracts import TokenBridgeHelper
from scripts.environment import get_tezos_client


@click.command()
@click.option(
    # TODO: consider renaming to `--helper`
    '--token-bridge-helper-address',
    required=True,
    help='The address of the Tezos Token Bridge Helper contract.',
)
@click.option(
    '--amount', required=True, type=int, help='The amount of tokens to be deposited.'
)
# TODO: consider making mandatory
@click.option(
    # TODO: consider renaming to `--to`
    '--receiver-address',
    default=None,
    help='The address of the Etherlink receiver contract which should receive token.',
)
@click.option(
    '--rollup-address', default=None, help='The address of the rollup contract.'
)
@click.option(
    '--private-key',
    default=None,
    help='Private key of the account on the Tezos network that should deposit token.',
)
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def deposit(
    token_bridge_helper_address: str,
    amount: int,
    receiver_address: Optional[str],
    rollup_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> str:
    """Deposits given amount of given token to the Etherlink Bridge"""

    # TODO: using L2_PUBLIC_KEY for receiver_address is implicit logic
    receiver_address = receiver_address or load_or_ask('L2_PUBLIC_KEY')
    rollup_address = rollup_address or load_or_ask('L1_ROLLUP_ADDRESS')
    receiver_address = receiver_address.replace('0x', '')
    receiver_bytes = bytes.fromhex(receiver_address)

    manager = get_tezos_client(rpc_url, private_key)
    token_bridge_helper = TokenBridgeHelper.from_address(
        manager, token_bridge_helper_address
    )
    token = token_bridge_helper.get_ticketer().get_token()

    opg = manager.bulk(
        token.disallow(manager, token_bridge_helper),
        token.allow(manager, token_bridge_helper),
        token_bridge_helper.deposit(rollup_address, receiver_bytes, amount),
    ).send()
    manager.wait(opg)
    operation_hash: str = opg.hash()
    print(f'Succeed, transaction hash: {operation_hash}')
    return operation_hash
