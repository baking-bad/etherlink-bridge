import click
from web3.types import HexBytes  # type: ignore
from scripts.helpers.utility import (
    get_etherlink_web3,
    get_etherlink_account,
)
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
    format_int,
)
from scripts.helpers.etherlink import (
    XtzWithdrawalPrecompileHelper,
    load_contract_type,
    make_filename,
)
from scripts import cli_options


@click.command()
@click.option(
    '--amount',
    required=True,
    type=int,
    default=1_000_000_000_000_000_000,
    prompt='Amount (wei)',
    help='The amount of xtz to withdraw in wei. Note that 1 xtz on Etherlink side is 10**18 wei. NOTE: it is impossible to withdraw values that have residuals less than 1 mutez (10**12 wei).',
)
@cli_options.receiver_address
@cli_options.xtz_withdraw_precompile
@cli_options.etherlink_private_key
@cli_options.etherlink_rpc_url
def xtz_withdraw(
    amount: int,
    receiver_address: str,
    xtz_withdraw_precompile: str,
    etherlink_private_key: str,
    etherlink_rpc_url: str,
) -> str:
    """Withdraws XTZ from L2 back to L1"""

    web3 = get_etherlink_web3(etherlink_rpc_url)
    account = get_etherlink_account(web3, etherlink_private_key)

    click.echo('Making XTZ withdrawal from ' + wrap(accent(account.address)) + ':')
    echo_variable('  - ', 'Executor', account.address)
    echo_variable('  - ', 'Etherlink RPC node', etherlink_rpc_url)
    click.echo('  - Withdrawal params:')
    echo_variable('      * ', 'Receiver', receiver_address)
    echo_variable('      * ', 'Amount (wei):', format_int(amount))
    echo_variable('      * ', 'Amount (mutez):', format_int(amount // 10**12))

    xtz_withdrawal_precompile = XtzWithdrawalPrecompileHelper.from_address(
        # TODO: consider adding XtzWithdrawalPrecompile ABI to the repo
        contract_type=load_contract_type(web3, make_filename('KernelMock')),
        web3=web3,
        account=account,
        # TODO: check: is it required `0x` to be added?
        address=xtz_withdraw_precompile,
    )

    receipt = xtz_withdrawal_precompile.withdraw(receiver_address, amount)
    tx_hash: HexBytes = receipt.transactionHash  # type: ignore
    click.echo(
        'Successfully initiated XTZ withdrawal, tx hash: ' + wrap(accent(tx_hash.hex()))
    )
    return tx_hash.hex()
