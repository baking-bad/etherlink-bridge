import click
from scripts.helpers.contracts.token_bridge_helper import TokenBridgeHelper
from scripts.helpers.utility import get_tezos_client
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options


@click.command()
@cli_options.token_bridge_helper_address
@cli_options.amount
@cli_options.receiver_address
@cli_options.smart_rollup_address
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
# TODO: consider renaming to fa_deposit
def deposit(
    token_bridge_helper_address: str,
    amount: int,
    receiver_address: str,
    smart_rollup_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
) -> str:
    """Deposits given amount of given token to the Etherlink Bridge"""

    receiver_bytes = bytes.fromhex(receiver_address.replace('0x', ''))
    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    token_bridge_helper = TokenBridgeHelper.from_address(
        manager, token_bridge_helper_address
    )
    ticketer = token_bridge_helper.get_ticketer()
    token = ticketer.get_token()
    # TODO: validate manager has tokens in the token contract

    click.echo(
        'Making deposit using Helper ' + wrap(accent(token_bridge_helper_address)) + ':'
    )
    echo_variable('  - ', 'Executor', manager.key.public_key_hash())
    echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
    echo_variable('  - ', 'Ticketer', ticketer.address)
    click.echo('  - Deposit params:')
    # TODO: add info about Token: type, addres, id
    # TODO: add Etherlink side ERC20 Proxy address here too
    echo_variable('      * ', 'Smart Rollup address', smart_rollup_address)
    echo_variable('      * ', 'Receiver address', receiver_address)
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
