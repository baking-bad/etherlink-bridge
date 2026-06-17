import click
from eth_abi import encode  # type: ignore
from scripts.helpers.tezosx_nac import (
    get_michelson_l2_client,
    ensure_revealed,
    nac_call_evm,
    FA_BRIDGE,
    TEZOSX_GATEWAY,
)
from scripts.helpers.utility import make_address_bytes
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options

# Solidity signature of FABridge.withdraw; the kernel derives the selector from it.
FA_WITHDRAW_SIG = 'withdraw(address,bytes,uint256,bytes22,bytes)'


def fa_withdraw_michelson(
    erc20_proxy_address: str,
    tezos_side_router_address: str,
    amount: int,
    ticketer_address_bytes: str,
    ticket_content_bytes: str,
    receiver_address: str,
    tezos_private_key: str,
    tezos_michelson_rpc_url: str,
) -> str:
    """Withdraws a wrapped FA token (ERC20) from the Michelson L2 to L1 (Tezos X only).

    The Michelson account issues a NAC `%call_evm` to the FA bridge precompile
    `withdraw(address,bytes,uint256,bytes22,bytes)`. Same arguments as the
    EVM-side `fa_withdraw`; the ERC20 is burned from the caller's alias.
    """

    routing_info = bytes.fromhex(
        make_address_bytes(receiver_address)
        + make_address_bytes(tezos_side_router_address)
    )
    ticketer = bytes.fromhex(ticketer_address_bytes.replace('0x', ''))
    content = bytes.fromhex(ticket_content_bytes.replace('0x', ''))
    abi_params = encode(
        ['address', 'bytes', 'uint256', 'bytes22', 'bytes'],
        [erc20_proxy_address, routing_info, amount, ticketer, content],
    )
    manager = get_michelson_l2_client(tezos_michelson_rpc_url, tezos_private_key)

    click.echo(
        'Making FA withdrawal from Michelson L2 via NAC gateway '
        + wrap(accent(TEZOSX_GATEWAY))
        + ':'
    )
    echo_variable('  - ', 'Executor', manager.key.public_key_hash())
    echo_variable('  - ', 'Michelson L2 RPC node', tezos_michelson_rpc_url)
    reveal_hash = ensure_revealed(manager)
    if reveal_hash:
        echo_variable('  - ', 'Revealed public key, tx hash', reveal_hash)
    click.echo('  - Withdrawal params:')
    echo_variable('      * ', 'FA bridge', FA_BRIDGE)
    echo_variable('      * ', 'Ticket owner (ERC20)', erc20_proxy_address)
    echo_variable('      * ', 'Receiver (L1)', receiver_address)
    echo_variable('      * ', 'Router', tezos_side_router_address)
    echo_variable('      * ', 'Routing info', '0x' + routing_info.hex())
    echo_variable('      * ', 'Amount', format_int(amount))
    echo_variable('      * ', 'Ticketer address bytes', '0x' + ticketer.hex())
    echo_variable('      * ', 'Content bytes', '0x' + content.hex())

    opg = nac_call_evm(
        manager,
        destination=FA_BRIDGE,
        method_sig=FA_WITHDRAW_SIG,
        abi_params=abi_params,
    )
    operation_hash: str = opg.hash()
    click.echo(
        'Successfully initiated FA withdrawal, tx hash: '
        + wrap(accent(operation_hash))
    )
    return operation_hash


fa_withdraw_michelson_command = cli_options.command(
    fa_withdraw_michelson,
    name='fa_withdraw_michelson',
    options=[
        cli_options.erc20_proxy_address,
        cli_options.tezos_side_router_address,
        cli_options.amount,
        cli_options.ticketer_address_bytes,
        cli_options.ticket_content_bytes,
        cli_options.receiver_address,
        cli_options.tezos_private_key,
        cli_options.tezos_michelson_rpc_url,
    ],
)
