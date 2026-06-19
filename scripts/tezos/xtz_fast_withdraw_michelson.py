import click
from eth_abi import encode  # type: ignore
from scripts.helpers.tezosx_nac import (
    get_michelson_l2_client,
    ensure_revealed,
    nac_call_evm,
    XTZ_BRIDGE,
    TEZOSX_GATEWAY,
)
from scripts.helpers.utility import pack
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts import cli_options


fast_withdrawal_contract_option = click.option(
    '--fast-withdrawal-contract',
    required=True,
    show_default=True,
    help='The Fast Withdrawal contract (KT1) on L1 that fronts the funds and '
    'later redeems the ticket from the Smart Rollup.',
)

discounted_amount_option = click.option(
    '--discounted-amount',
    required=True,
    type=int,
    prompt='Discounted withdrawal amount (mutez)',
    help='Amount (mutez) the Service Provider accepts to front the withdrawal; '
    'the difference from --amount is their fee. Packed into the payload as a nat.',
)


def xtz_fast_withdraw_michelson(
    amount: int,
    receiver_address: str,
    fast_withdrawal_contract: str,
    discounted_amount: int,
    tezos_private_key: str,
    tezos_michelson_rpc_url: str,
) -> str:
    """Fast-withdraws XTZ from the Michelson L2 to L1 (Tezos X only).

    Like `xtz_withdraw_michelson`, but issues the NAC `%call_evm` against the XTZ
    bridge precompile's `fast_withdraw_base58(string,string,bytes)` instead of the
    plain `withdraw_base58`: the Service Provider at `--fast-withdrawal-contract`
    fronts `--discounted-amount` mutez to the L1 receiver immediately and later
    redeems the full `--amount` ticket from the Smart Rollup. `amount` mutez is
    forwarded as the EVM `msg.value`; `--receiver-address` is the L1 base58 target.
    """

    payload = pack(discounted_amount, 'nat')
    abi_params = encode(
        ['string', 'string', 'bytes'],
        [receiver_address, fast_withdrawal_contract, payload],
    )
    manager = get_michelson_l2_client(tezos_michelson_rpc_url, tezos_private_key)

    click.echo(
        'Making XTZ Fast Withdrawal from Michelson L2 via NAC gateway '
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
    echo_variable('      * ', 'Fast Withdrawal contract', fast_withdrawal_contract)
    echo_variable('      * ', 'Payload bytes', payload.hex())
    echo_variable('      * ', 'Amount (mutez)', format_int(amount))
    echo_variable('      * ', 'Discounted amt (mutez)', format_int(discounted_amount))
    echo_variable('      * ', 'Fee (mutez)', format_int(amount - discounted_amount))

    opg = nac_call_evm(
        manager,
        destination=XTZ_BRIDGE,
        method_sig='fast_withdraw_base58(string,string,bytes)',
        abi_params=abi_params,
        amount_mutez=amount,
    )
    operation_hash: str = opg.hash()
    click.echo(
        'Successfully initiated XTZ Fast Withdrawal, tx hash: '
        + wrap(accent(operation_hash))
    )
    return operation_hash


xtz_fast_withdraw_michelson_command = cli_options.command(
    xtz_fast_withdraw_michelson,
    name='xtz_fast_withdraw_michelson',
    options=[
        cli_options.amount,
        cli_options.receiver_address,
        fast_withdrawal_contract_option,
        discounted_amount_option,
        cli_options.tezos_private_key,
        cli_options.tezos_michelson_rpc_url,
    ],
)
