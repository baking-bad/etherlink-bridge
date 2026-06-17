import click
from scripts.helpers.utility import get_tezos_client
from scripts.helpers.alias import compute_alias, alias_bytes
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options


def xtz_deposit_alias(
    xtz_ticket_helper: str,
    amount: int,
    receiver_address: str,
    smart_rollup_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
) -> str:
    """Deposits XTZ to a Michelson L2 tz* via its EVM alias on the Etherlink side.

    Same path as `xtz_deposit`, but `--receiver-address` is a Michelson L2
    address (tz*): we deposit to its EVM alias, which forwards to the native
    account once the alias is initialised.
    """

    receiver_bytes = alias_bytes(receiver_address)
    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    helper = manager.contract(xtz_ticket_helper)

    click.echo(
        'Making XTZ deposit to Michelson L2 alias using Helper '
        + wrap(accent(xtz_ticket_helper))
        + ':'
    )
    echo_variable('  - ', 'Executor', manager.key.public_key_hash())
    echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
    click.echo('  - XTZ deposit params:')
    echo_variable('      * ', 'Smart Rollup address', smart_rollup_address)
    echo_variable('      * ', 'Michelson L2 receiver', receiver_address)
    echo_variable('      * ', 'EVM alias', compute_alias(receiver_address))
    echo_variable('      * ', 'Amount (mutez)', format_int(amount))

    opg = (
        helper.deposit(
            {
                'evm_address': smart_rollup_address,
                'l2_address': receiver_bytes,
            }
        )
        .with_amount(amount)
        .send()
    )
    manager.wait(opg)
    operation_hash: str = opg.hash()
    click.echo(
        'Successfully executed XTZ deposit, tx hash: ' + wrap(accent(operation_hash))
    )
    return operation_hash


xtz_deposit_alias_command = cli_options.command(
    xtz_deposit_alias,
    name='xtz_deposit_alias',
    options=[
        cli_options.xtz_ticket_helper,
        cli_options.amount,
        cli_options.receiver_address,
        cli_options.smart_rollup_address,
        cli_options.tezos_private_key,
        cli_options.tezos_rpc_url,
    ],
)
