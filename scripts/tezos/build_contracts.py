import click
from scripts.tezos.compile_contract import compile_contract


@click.command()
@click.option(
    '--ligo-version',
    default='1.3.0',
    help='LIGO compiler version used to compile Tezos side contracts, default: 1.3.0',
)
def build_contracts(
    ligo_version: str,
) -> None:
    """Compiles Tezos side contracts using dockerized LIGO compiler."""

    # TODO: consider removing everything from build directory before compiling

    click.echo('Compiling Tezos side contracts:')
    compile_contract.callback(
        ligo_version,
        'contracts/ticket-router-tester/ticket-router-tester.mligo',
        'TicketRouterTester',
    )  # type: ignore

    compile_contract.callback(
        ligo_version,
        'contracts/token-bridge-helper/token-bridge-helper.mligo',
        'TokenBridgeHelper',
    )  # type: ignore

    compile_contract.callback(
        ligo_version,
        'contracts/rollup-mock/rollup-mock.mligo',
        'RollupMock',
    )  # type: ignore

    compile_contract.callback(
        ligo_version,
        'contracts/ticketer/ticketer.mligo',
        'Ticketer',
    )  # type: ignore

    compile_contract.callback(
        ligo_version,
        'contracts/metadata-tracker/metadata-tracker.mligo',
        'MetadataTracker',
    )  # type: ignore

    click.echo('Done')


@click.command()
@click.option(
    '--ligo-version',
    default='1.9.2',
    help='LIGO compiler version used to compile Tezos side contracts, default: 1.9.2',
)
def build_fast_withdrawal(
    ligo_version: str,
) -> None:
    """Compiles Tezos side contracts using dockerized LIGO compiler."""

    compile_contract.callback(
        ligo_version,
        'contracts/fast-withdrawal/fast-withdrawal.mligo',
    )  # type: ignore

    compile_contract.callback(
        ligo_version,
        'contracts/purchase-withdrawal-proxy/purchase-withdrawal-proxy.mligo',
    )  # type: ignore

    compile_contract.callback(
        ligo_version,
        'contracts/ticket-router-tester/ticket-router-tester.mligo',
        'TicketRouterTester',
    )  # type: ignore

    click.echo('Done')
