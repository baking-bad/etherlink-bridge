import click
import rlp
from pytezos.michelson.forge import forge_address

from scripts.helpers.utility import get_tezos_client
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options


def michelson_routing_data(receiver: str) -> bytes:
    """V1 RLP routing data for an L1 -> Michelson L2 (Tezlink) deposit:
    `[version=0x01] ++ rlp([[tag=0x01, forged receiver], none])`."""

    forged = forge_address(receiver)
    if forged[0] != 0x00:  # 0x00 = implicit, 0x01 = originated (KT1)
        raise click.BadParameter(
            f'Michelson L2 receiver must be an implicit account (tz*), '
            f'got {receiver}: the kernel rejects deposits to smart contracts.'
        )
    return bytes([1]) + bytes(rlp.encode([[b'\x01', forged], []]))


def xtz_deposit_michelson(
    xtz_ticket_helper: str,
    amount: int,
    receiver_address: str,
    smart_rollup_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
) -> str:
    """Deposits given amount of XTZ to a tz* receiver on the Michelson L2 (Tezos X only)"""

    routing_data = michelson_routing_data(receiver_address)
    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    helper = manager.contract(xtz_ticket_helper)

    click.echo(
        'Making XTZ deposit to Michelson L2 using Helper '
        + wrap(accent(xtz_ticket_helper))
        + ':'
    )
    echo_variable('  - ', 'Executor', manager.key.public_key_hash())
    echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
    click.echo('  - XTZ deposit params:')
    echo_variable('      * ', 'Smart Rollup address', smart_rollup_address)
    echo_variable('      * ', 'Receiver address', receiver_address)
    echo_variable('      * ', 'Routing data', '0x' + routing_data.hex())
    echo_variable('      * ', 'Amount (mutez)', format_int(amount))

    opg = (
        helper.deposit(
            {
                'evm_address': smart_rollup_address,
                'l2_address': routing_data,
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


xtz_deposit_michelson_command = cli_options.command(
    xtz_deposit_michelson,
    name='xtz_deposit_michelson',
    options=[
        cli_options.xtz_ticket_helper,
        cli_options.amount,
        cli_options.receiver_address,
        cli_options.smart_rollup_address,
        cli_options.tezos_private_key,
        cli_options.tezos_rpc_url,
    ],
)
