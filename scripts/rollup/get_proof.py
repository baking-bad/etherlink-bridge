import click
from scripts.helpers.proof import get_proof as get_proof_from_rpc, Proof
from scripts import cli_options
from scripts.helpers.utility import accent


@click.command()
@click.option('--level', required=True, type=int, help='The level of the outbox.')
@click.option('--index', required=True, type=int, help='The index of the message.')
@cli_options.etherlink_rollup_node_url
@cli_options.silent
def get_proof(
    level: int,
    index: int,
    etherlink_rollup_node_url: str,
    silent: bool,
) -> Proof:
    """Makes call to the RPC and returns proof info required to execute outbox_message"""

    level_and_index = 'level ' + accent(str(level)) + ', index ' + accent(str(index))
    proof = get_proof_from_rpc(etherlink_rollup_node_url, level, index)
    if 'commitment' in proof:
        if not silent:
            click.echo('Outbox message at ' + level_and_index + ':')
            click.echo('  - Commitment: `' + accent(proof['commitment']) + '`')
            click.echo('  - Proof: `' + accent(proof['proof']) + '`')
        return proof

    click.echo('Failed to get proof for outbox message at ' + level_and_index + '.')
