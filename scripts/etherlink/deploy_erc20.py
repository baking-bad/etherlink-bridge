import click
from scripts.helpers.utility import (
    get_etherlink_web3,
    get_etherlink_account,
)
from scripts.helpers.formatting import (
    accent,
    echo_variable,
    wrap,
)
from scripts.helpers.etherlink import (
    Erc20ProxyHelper,
    make_filename,
)
from scripts import cli_options


@click.command()
# TODO: consider replacing two bytes options with one ticketer_address option
@cli_options.ticketer_address_bytes
@cli_options.ticket_content_bytes
# TODO: consider extracting token name from the ticketer content bytes
@cli_options.token_name
@cli_options.token_symbol
@cli_options.token_decimals
@cli_options.kernel_address
@cli_options.etherlink_private_key
@cli_options.etherlink_rpc_url
@cli_options.skip_confirm
@cli_options.silent
# TODO: consider adding gas price and gas limit here as parameters?
def deploy_erc20(
    ticketer_address_bytes: str,
    ticket_content_bytes: str,
    token_name: str,
    token_symbol: str,
    token_decimals: int,
    kernel_address: str,
    etherlink_private_key: str,
    etherlink_rpc_url: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> Erc20ProxyHelper:
    """Deploys ERC20 Proxy contract with given parameters"""

    web3 = get_etherlink_web3(etherlink_rpc_url)
    account = get_etherlink_account(web3, etherlink_private_key)
    ticketer = bytes.fromhex(ticketer_address_bytes.replace('0x', ''))
    content = bytes.fromhex(ticket_content_bytes.replace('0x', ''))

    if not silent:
        click.echo('Deploying ERC20 Proxy for ' + wrap(accent(token_symbol)) + ':')
        echo_variable('  - ', 'Deployer', account.address)
        echo_variable('  - ', 'Etherlink RPC node', etherlink_rpc_url)
        click.echo('  - Constructor params:')
        echo_variable('      * ', 'Ticketer address bytes', '0x' + ticketer.hex())
        echo_variable('      * ', 'Content bytes', '0x' + content.hex())
        echo_variable('      * ', 'Kernel address', kernel_address)
        echo_variable('      * ', 'Name', token_name)
        echo_variable('      * ', 'Symbol', token_symbol)
        echo_variable('      * ', 'Decimals', str(token_decimals))
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    erc20 = Erc20ProxyHelper.originate_from_file(
        web3=web3,
        account=account,
        filename=make_filename('ERC20Proxy'),
        constructor_args=(
            ticketer,
            content,
            kernel_address,
            token_name,
            token_symbol,
            token_decimals,
        ),
    )

    if not silent:
        click.echo(
            'Successfully deployed ERC20 Proxy token, address: '
            + wrap(accent(erc20.address))
        )
    return erc20
