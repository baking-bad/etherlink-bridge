import click
from scripts.helpers.contracts import PurchaseWithdrawalProxy
from scripts.helpers.utility import get_tezos_client
from scripts.helpers.formatting import (
    accent,
    wrap,
    echo_variable,
)
from scripts import cli_options


@click.command()
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.skip_confirm
@cli_options.silent
def deploy_purchase_withdrawal_proxy(
    tezos_private_key: str,
    tezos_rpc_url: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> PurchaseWithdrawalProxy:
    """Deploys `purchase_withdrawal_proxy` contract with dummy storage"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)

    if not silent:
        click.echo('Deploying Purchase Withdrawal Proxy contract:')
        echo_variable('  - ', 'Deployer', manager.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)

    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    opg = PurchaseWithdrawalProxy.originate(
        client=manager,
    ).send()
    manager.wait(opg)
    purchase_withdrawal_proxy = PurchaseWithdrawalProxy.from_opg(manager, opg)
    if not silent:
        click.echo(
            'Successfully deployed Purchase Withrawal Proxy, address: '
            + wrap(accent(purchase_withdrawal_proxy.address))
        )

    return purchase_withdrawal_proxy
