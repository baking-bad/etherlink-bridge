import click
from typing import Optional
from scripts.environment import load_or_ask, get_tezos_client


@click.command()
@click.option(
    '--commitment', required=True, help='The commitment of the outbox message.'
)
@click.option('--proof', required=True, help='The proof of the outbox message.')
@click.option(
    '--rollup-address', default=None, help='The address of the rollup contract.'
)
@click.option(
    '--private-key',
    default=None,
    help='Private key that would be used to execute message on the Tezos network.',
)
@click.option('--rpc-url', default=None, help='Tezos RPC URL.')
def execute_outbox_message(
    commitment: str,
    proof: str,
    rollup_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Executes outbox message using provided `commitment` and `proof`"""

    rollup_address = rollup_address or load_or_ask('L1_ROLLUP_ADDRESS')
    # TODO: consider print the address of rollup contract
    manager = get_tezos_client(rpc_url, private_key)
    opg = manager.smart_rollup_execute_outbox_message(
        rollup_address, commitment, bytes.fromhex(proof)
    ).send()
    manager.wait(opg)
    print(f'Succeed, transaction hash: {opg.hash()}')
