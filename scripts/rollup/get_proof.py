import click
from typing import Optional
from scripts.helpers.proof import get_proof as get_proof_from_rpc, Proof
from scripts.environment import load_or_ask


@click.command()
@click.option('--level', required=True, type=int, help='The level of the outbox.')
@click.option('--index', required=True, type=int, help='The index of the message.')
@click.option('--rollup-rpc-url', default=None, help='Etherlink Rollup RPC URL.')
def get_proof(
    level: int,
    index: int,
    rollup_rpc_url: Optional[str],
) -> Proof:
    """Makes call to the RPC and returns proof info required to execute outbox_message"""

    rollup_rpc_url = rollup_rpc_url or load_or_ask('L2_ROLLUP_RPC_URL')
    proof = get_proof_from_rpc(rollup_rpc_url, level, index)
    if 'commitment' in proof:
        print(f'commitment: {proof["commitment"]}')
        print(f'proof: {proof["proof"]}')
        return proof

    print('Something went wrong:')
    print(proof)
