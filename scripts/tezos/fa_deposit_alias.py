import click
from scripts.helpers.contracts.token_bridge_helper import TokenBridgeHelper
from scripts.helpers.utility import get_tezos_client
from scripts.helpers.alias import compute_alias, alias_bytes
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options


def fa_deposit_alias(
    token_bridge_helper_address: str,
    amount: int,
    receiver_address: str,
    smart_rollup_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
) -> str:
    """Deposits an FA token to a Michelson L2 tz* via its EVM alias.

    Same path as `fa_deposit`, but `--receiver-address` is a Michelson L2
    address (tz*): we deposit to its EVM alias, which forwards to the native
    account once the alias is initialised.
    """

    receiver_bytes = alias_bytes(receiver_address)
    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    token_bridge_helper = TokenBridgeHelper.from_address(
        manager, token_bridge_helper_address
    )
    ticketer = token_bridge_helper.get_ticketer()
    token = ticketer.get_token()

    click.echo(
        'Making deposit to Michelson L2 alias using Helper '
        + wrap(accent(token_bridge_helper_address))
        + ':'
    )
    echo_variable('  - ', 'Executor', manager.key.public_key_hash())
    echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
    echo_variable('  - ', 'Ticketer', ticketer.address)
    click.echo('  - Deposit params:')
    echo_variable('      * ', 'Smart Rollup address', smart_rollup_address)
    echo_variable('      * ', 'Michelson L2 receiver', receiver_address)
    echo_variable('      * ', 'EVM alias', compute_alias(receiver_address))
    echo_variable('      * ', 'Amount', format_int(amount))

    opg = manager.bulk(
        token.disallow(manager, token_bridge_helper),
        token.allow(manager, token_bridge_helper),
        token_bridge_helper.deposit(smart_rollup_address, receiver_bytes, amount),
    ).send()
    manager.wait(opg)
    operation_hash: str = opg.hash()
    click.echo(
        'Successfully executed Deposit, tx hash: ' + wrap(accent(operation_hash))
    )
    return operation_hash


fa_deposit_alias_command = cli_options.command(
    fa_deposit_alias,
    name='fa_deposit_alias',
    options=[
        cli_options.token_bridge_helper_address,
        cli_options.amount,
        cli_options.receiver_address,
        cli_options.smart_rollup_address,
        cli_options.tezos_private_key,
        cli_options.tezos_rpc_url,
    ],
)
