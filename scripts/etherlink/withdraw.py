import click
from web3.types import HexBytes  # type: ignore
from scripts.helpers.utility import (
    get_etherlink_web3,
    get_etherlink_account,
    make_address_bytes,
    accent,
    echo_variable,
    wrap,
)
from scripts.helpers.etherlink import (
    FaWithdrawalPrecompileHelper,
    load_contract_type,
    make_filename,
)
from scripts import cli_options


@click.command()
@cli_options.erc20_proxy_address
@cli_options.tezos_side_router_address
@cli_options.amount
# TODO: consider get ticketer address bytes and content from the ticketer address?
#       However, the tezos rpc node is required to get the ticketer params.
@cli_options.ticketer_address_bytes
@cli_options.ticket_content_bytes
@cli_options.receiver_address
@cli_options.withdraw_precompile
@cli_options.etherlink_private_key
@cli_options.etherlink_rpc_url
def withdraw(
    erc20_proxy_address: str,
    tezos_side_router_address: str,
    amount: int,
    ticketer_address_bytes: str,
    ticket_content_bytes: str,
    receiver_address: str,
    withdraw_precompile: str,
    etherlink_private_key: str,
    etherlink_rpc_url: str,
) -> str:
    """Withdraws provided wrapped FA token (ERC20) from L2 back to L1"""

    web3 = get_etherlink_web3(etherlink_rpc_url)
    account = get_etherlink_account(web3, etherlink_private_key)
    receiver_address_bytes = make_address_bytes(receiver_address)
    router_address_bytes = make_address_bytes(tezos_side_router_address)
    routing_info_str = receiver_address_bytes + router_address_bytes
    routing_info = bytes.fromhex(routing_info_str)
    ticketer = bytes.fromhex(ticketer_address_bytes.replace('0x', ''))
    content = bytes.fromhex(ticket_content_bytes.replace('0x', ''))

    click.echo(
        'Making FA withdrawal, ERC20 token: ' + wrap(accent(erc20_proxy_address)) + ':'
    )
    echo_variable('  - ', 'Executor', account.address)
    echo_variable('  - ', 'Etherlink RPC node', etherlink_rpc_url)
    click.echo('  - Withdrawal params:')
    echo_variable('      * ', 'Ticket owner', erc20_proxy_address)
    echo_variable('      * ', 'Receiver', receiver_address)
    echo_variable('      * ', 'Router', tezos_side_router_address)
    echo_variable('      * ', 'Routing info', '0x' + routing_info.hex())
    echo_variable('      * ', 'Amount', str(amount))
    echo_variable('      * ', 'Ticketer address bytes', '0x' + ticketer.hex())
    echo_variable('      * ', 'Content bytes', '0x' + content.hex())

    fa_withdrawal_precompile = FaWithdrawalPrecompileHelper.from_address(
        # TODO: consider adding FaWithdrawalPrecompile ABI to the repo
        contract_type=load_contract_type(web3, make_filename('KernelMock')),
        web3=web3,
        account=account,
        # TODO: check: is it required `0x` to be added?
        address=withdraw_precompile,
    )

    receipt = fa_withdrawal_precompile.withdraw(
        ticket_owner=erc20_proxy_address,
        routing_info=routing_info,
        amount=amount,
        ticketer=ticketer,
        content=content,
    )

    tx_hash: HexBytes = receipt.transactionHash  # type: ignore
    click.echo(
        'Successfully initiated FA withdrawal, tx hash: ' + wrap(accent(tx_hash.hex()))
    )
    return tx_hash.hex()
