import click
from scripts.defaults import EXCHANGER_ADDRESS
from scripts.helpers.contracts import FastWithdrawal
from scripts.helpers.utility import get_tezos_client
from scripts.helpers.formatting import (
    accent,
    wrap,
    echo_variable,
)
from scripts import cli_options


@click.command()
@click.option(
    '--exchanger-address',
    default=EXCHANGER_ADDRESS,
    envvar='EXCHANGER_ADDRESS',
    required=True,
    prompt='Exchanger contract (native XTZ ticketer) address',
    help='The address of the Exchanger contract that wraps XTZ on Tezos side.',
    show_default=True,
)
@cli_options.smart_rollup_address
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.skip_confirm
@cli_options.silent
def deploy_fast_withdrawal(
    exchanger_address: str,
    smart_rollup_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> FastWithdrawal:
    """Deploys `fast_withdrawal` contract for provided Exchanger"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)

    if not silent:
        click.echo('Deploying Fast Withdrawal contract:')
        echo_variable('  - ', 'Deployer', manager.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
        click.echo('  - Params:')
        echo_variable('      * ', 'Exchanger address', exchanger_address)
        echo_variable('      * ', 'Smart Rollup address', smart_rollup_address)
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    opg = FastWithdrawal.originate(
        client=manager,
        exchanger=exchanger_address,
        smart_rollup=smart_rollup_address,
    ).send()
    manager.wait(opg)
    fast_withdrawal = FastWithdrawal.from_opg(manager, opg)
    if not silent:
        click.echo(
            'Successfully deployed Fast Withdrawal, address: '
            + wrap(accent(fast_withdrawal.address))
        )

    return fast_withdrawal
