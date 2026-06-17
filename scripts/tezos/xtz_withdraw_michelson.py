import click
from eth_abi import encode  # type: ignore
from scripts.helpers.tezosx_nac import (
    get_michelson_l2_client,
    ensure_revealed,
    nac_call_evm,
    XTZ_BRIDGE,
    TEZOSX_GATEWAY,
)
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options


def xtz_withdraw_michelson(
    amount: int,
    receiver_address: str,
    tezos_private_key: str,
    tezos_michelson_rpc_url: str,
) -> str:
    """Withdraws XTZ from the Michelson L2 to L1 (Tezos X only).

    The Michelson account issues a NAC `%call_evm` to the XTZ bridge precompile
    `withdraw_base58(string)`, forwarding `amount` mutez as the EVM `msg.value`.
    `--receiver-address` is the L1 (shadownet) base58 receiver.
    """

    abi_params = encode(['string'], [receiver_address])
    manager = get_michelson_l2_client(tezos_michelson_rpc_url, tezos_private_key)

    click.echo(
        'Making XTZ withdrawal from Michelson L2 via NAC gateway '
        + wrap(accent(TEZOSX_GATEWAY))
        + ':'
    )
    echo_variable('  - ', 'Executor', manager.key.public_key_hash())
    echo_variable('  - ', 'Michelson L2 RPC node', tezos_michelson_rpc_url)
    reveal_hash = ensure_revealed(manager)
    if reveal_hash:
        echo_variable('  - ', 'Revealed public key, tx hash', reveal_hash)
    click.echo('  - Withdrawal params:')
    echo_variable('      * ', 'XTZ bridge', XTZ_BRIDGE)
    echo_variable('      * ', 'Receiver (L1)', receiver_address)
    echo_variable('      * ', 'Amount (mutez)', format_int(amount))

    opg = nac_call_evm(
        manager,
        destination=XTZ_BRIDGE,
        method_sig='withdraw_base58(string)',
        abi_params=abi_params,
        amount_mutez=amount,
    )
    operation_hash: str = opg.hash()
    click.echo(
        'Successfully initiated XTZ withdrawal, tx hash: '
        + wrap(accent(operation_hash))
    )
    return operation_hash


xtz_withdraw_michelson_command = cli_options.command(
    xtz_withdraw_michelson,
    name='xtz_withdraw_michelson',
    options=[
        cli_options.amount,
        cli_options.receiver_address,
        cli_options.tezos_private_key,
        cli_options.tezos_michelson_rpc_url,
    ],
)
