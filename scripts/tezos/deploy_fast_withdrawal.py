import click
from scripts.defaults import XTZ_TICKETER_ADDRESS
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
    '--xtz-ticketer-address',
    default=XTZ_TICKETER_ADDRESS,
    envvar='XTZ_TICKETER_ADDRESS',
    required=True,
    prompt='Native XTZ Ticketer contract (exchanger) address',
    help='The address of the Native XTZ Ticketer contract that wraps XTZ on Tezos side.',
    show_default=True,
)
# TODO: add expiration_seconds parameter
@cli_options.smart_rollup_address
@cli_options.tezos_private_key
@cli_options.tezos_rpc_url
@cli_options.skip_confirm
@cli_options.silent
def deploy_fast_withdrawal(
    xtz_ticketer_address: str,
    smart_rollup_address: str,
    tezos_private_key: str,
    tezos_rpc_url: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> FastWithdrawal:
    """Deploys `fast_withdrawal` contract"""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)

    if not silent:
        click.echo('Deploying Fast Withdrawal contract:')
        echo_variable('  - ', 'Deployer', manager.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
        click.echo('  - Params:')
        echo_variable('      * ', 'Native XTZ Ticketer address', xtz_ticketer_address)
        echo_variable('      * ', 'Smart Rollup address', smart_rollup_address)
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    opg = FastWithdrawal.originate(
        client=manager,
        xtz_ticketer=xtz_ticketer_address,
        # TODO: expiration seconds to the parameter:
        expiration_seconds=60 * 60 * 24,
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
