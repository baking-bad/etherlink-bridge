import click
import subprocess
import os


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

    # TODO: consider making this a separate script to compile one contract:
    def compile_contract(
        contract_path: str,
        module_name: str,
        output_path: str,
    ) -> None:
        print(f'- Compiling {module_name} contract')
        cwd = os.path.join(os.getcwd(), 'tezos')
        result = subprocess.run(
            [
                'docker',
                'run',
                '--rm',
                '-v',
                f'{cwd}:{cwd}',
                '-w',
                cwd,
                f'ligolang/ligo:{ligo_version}',
                'compile',
                'contract',
                contract_path,
                '-m',
                module_name,
                '-o',
                output_path,
            ],
            # check=True,
            cwd=cwd,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

    if not os.path.exists('tezos/build'):
        os.makedirs('tezos/build')

    # TODO: consider removing everything from build directory before compiling

    print('Compiling Tezos side contracts:')
    compile_contract(
        'contracts/ticket-router-tester/ticket-router-tester.mligo',
        'TicketRouterTester',
        'build/ticket-router-tester.tz',
    )
    compile_contract(
        'contracts/token-bridge-helper/token-bridge-helper.mligo',
        'TokenBridgeHelper',
        'build/token-bridge-helper.tz',
    )
    compile_contract(
        'contracts/rollup-mock/rollup-mock.mligo',
        'RollupMock',
        'build/rollup-mock.tz',
    )
    compile_contract(
        'contracts/ticketer/ticketer.mligo',
        'Ticketer',
        'build/ticketer.tz',
    )
    compile_contract(
        'contracts/metadata-tracker/metadata-tracker.mligo',
        'MetadataTracker',
        'build/metadata-tracker.tz',
    )


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

    # TODO: remove code duplication (this fn doesn't require module to be provided):
    # two options:
    # 1. change contract so it will be a module too
    # 2. keep this as separate fn
    # 3. make some branching in the function
    def compile_contract(
        contract_path: str,
        output_path: str,
    ) -> None:
        print(f'- Compiling {contract_path} contract')
        cwd = os.path.join(os.getcwd(), 'tezos')
        result = subprocess.run(
            [
                'docker',
                'run',
                '--rm',
                '-v',
                f'{cwd}:{cwd}',
                '-w',
                cwd,
                f'ligolang/ligo:{ligo_version}',
                'compile',
                'contract',
                contract_path,
                '-o',
                output_path,
            ],
            # check=True,
            cwd=cwd,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

    compile_contract(
        'contracts/fast-withdrawal/fast-withdrawal.mligo',
        'build/fast-withdrawal.tz',
    )
    print('Done')
