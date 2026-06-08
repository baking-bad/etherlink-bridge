import click
from scripts.helpers.utility import get_tezos_client
from scripts.helpers.formatting import accent
from scripts import cli_options


# TODO: consider simplifying by providing --level and --index instead?
commitment_option = click.option(
    '--commitment',
    required=True,
    prompt='Commitment with the outbox message',
    help='Commitment with the outbox message.',
)
proof_option = click.option(
    '--proof',
    required=True,
    prompt='The proof of the outbox message',
    help='The proof of the outbox message.',
)


def execute_outbox_message(
    commitment: str,
    proof: str,
    smart_rollup_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
) -> str:
    """Executes outbox message using provided `commitment` and `proof`"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    click.echo('Executing outbox message:')
    click.echo('  - Commitment: `' + accent(commitment) + '`')
    click.echo('  - Proof: `' + accent(proof) + '`')
    click.echo('  - Smart Rollup address: `' + accent(smart_rollup_address) + '`')
    click.echo('  - Executor: `' + accent(manager.key.public_key_hash()) + '`')
    click.echo('  - Tezos RPC node: `' + accent(tezos_rpc_url) + '`')

    opg = manager.smart_rollup_execute_outbox_message(
        smart_rollup_address, commitment, bytes.fromhex(proof)
    ).send()
    manager.wait(opg)
    operation_hash: str = opg.hash()
    click.echo(
        'Successfully executed outbox message, tx hash: `'
        + accent(operation_hash)
        + '`'
    )
    return operation_hash


execute_outbox_message_command = cli_options.command(
    execute_outbox_message,
    name='execute_outbox_message',
    options=[
        commitment_option,
        proof_option,
        cli_options.smart_rollup_address,
        cli_options.tezos_private_key,
        cli_options.tezos_rpc_url,
    ],
)
