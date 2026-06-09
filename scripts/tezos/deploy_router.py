import click

from scripts import cli_options
from scripts.helpers.contracts.ticket_router_tester import TicketRouterTester
from scripts.helpers.formatting import accent, echo_variable, wrap
from scripts.helpers.utility import get_tezos_client


def deploy_router(
    tezos_private_key: str,
    tezos_rpc_url: str,
    skip_confirm: bool = True,
    silent: bool = True,
) -> TicketRouterTester:
    """Deploys the `ticket-router-tester` contract using the provided key."""

    manager = get_tezos_client(tezos_rpc_url, tezos_private_key)
    if not silent:
        # No deploy params for this contract — show who/where, like the others.
        click.echo('Deploying ' + wrap(accent('TicketRouterTester')) + ':')
        echo_variable('  - ', 'Deployer', manager.key.public_key_hash())
        echo_variable('  - ', 'Tezos RPC node', tezos_rpc_url)
    if not skip_confirm:
        click.confirm('Do you want to proceed?', abort=True, default=True)

    opg = TicketRouterTester.originate(manager).send()
    manager.wait(opg)
    tester = TicketRouterTester.from_opg(manager, opg)
    if not silent:
        click.echo(
            'Successfully deployed TicketRouterTester, address: '
            + wrap(accent(tester.address))
        )

    return tester


deploy_router_command = cli_options.command(
    deploy_router,
    name='deploy_router',
    options=[
        cli_options.tezos_private_key,
        cli_options.tezos_rpc_url,
        cli_options.skip_confirm,
        cli_options.silent,
    ],
)
