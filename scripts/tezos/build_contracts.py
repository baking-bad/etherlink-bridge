import click
from scripts.tezos.compile_contract import compile_contract
from scripts import cli_options

ligo_version_option = click.option(
    '--ligo-version',
    default='1.9.2',
    help='LIGO compiler version used to compile Tezos side contracts, default: 1.9.2',
    show_default=True,
)


def build_contracts(ligo_version: str) -> None:
    """Compiles Tezos side contracts using dockerized LIGO compiler."""

    # TODO: consider removing everything from build directory before compiling

    click.echo('Compiling Tezos side contracts:')
    compile_contract(
        ligo_version,
        'contracts/ticket-router-tester/ticket-router-tester.mligo',
        'TicketRouterTester',
    )
    compile_contract(
        ligo_version,
        'contracts/token-bridge-helper/token-bridge-helper.mligo',
        'TokenBridgeHelper',
    )
    compile_contract(
        ligo_version,
        'contracts/rollup-mock/rollup-mock.mligo',
        'RollupMock',
    )
    compile_contract(
        ligo_version,
        'contracts/ticketer/ticketer.mligo',
        'Ticketer',
    )
    compile_contract(
        ligo_version,
        'contracts/metadata-tracker/metadata-tracker.mligo',
        'MetadataTracker',
    )
    click.echo('Done')


def build_fast_withdrawal(ligo_version: str) -> None:
    """Compiles Tezos side contracts using dockerized LIGO compiler."""

    compile_contract(
        ligo_version,
        'contracts/fast-withdrawal/fast-withdrawal.mligo',
    )
    compile_contract(
        ligo_version,
        'contracts/ticket-router-tester/ticket-router-tester.mligo',
        'TicketRouterTester',
    )
    click.echo('Done')


build_contracts_command = cli_options.command(
    build_contracts,
    name='build_tezos_contracts',
    options=[ligo_version_option],
)

build_fast_withdrawal_command = cli_options.command(
    build_fast_withdrawal,
    name='build_fast_withdrawal',
    options=[ligo_version_option],
)
