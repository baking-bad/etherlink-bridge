from dotenv import load_dotenv
from getpass import getpass
import os
import click
from dataclasses import dataclass


def load_or_ask(var_name: str, is_secret: bool = False) -> str:
    ask = getpass if is_secret else input
    return os.getenv(var_name) or ask(f'Enter {var_name}: ')  # type: ignore


@dataclass
class Variable:
    name: str
    default: str = ''
    is_secret: bool = False
    template: str = 'Enter "{name}" (default: {default}): '

    def ask(self) -> str:
        ask = getpass if self.is_secret else input
        question = self.template.format(name=self.name, default=self.default)
        return ask(question) or self.default  # type: ignore


@click.command()
def init_wallets() -> None:
    """Initialize wallets for the demo. Asks user for private keys and
    RPC URLs to create .env file with them."""

    if os.path.isfile('.env'):
        print('File .env already exists. Please remove it to avoid overwriting.')
        return

    variables = [
        Variable(
            'L1_PRIVATE_KEY',
            default='edsk4baRSdYGM7dkgasgGgHDr4Ge8BtRZBkx1Cq634dSRFez81MDhK',
            is_secret=True,
        ),
        # TODO: it is possible to get L1_PUBLIC_KEY_HASH from L1_PRIVATE_KEY
        Variable('L1_PUBLIC_KEY_HASH', default='tz1av2T75Wazm8UovatQB3wYD4tqUVfCcwrZ'),
        Variable('L1_RPC_URL', default='https://rpc.tzkt.io/oxfordnet/'),
        Variable('L1_ROLLUP_ADDRESS', default='sr1T4XVcVtBRzYy52edVTdgup9Kip4Wrmn97'),
        Variable(
            'L2_PRIVATE_KEY',
            default='f463e320ed1bd1cd833e29efc383878f34abe6b596e5d163f51bb8581de6f8b8',
            is_secret=True,
        ),
        # TODO: it is possible to get L2_PUBLIC_KEY from L2_PRIVATE_KEY
        Variable('L2_PUBLIC_KEY', default='0x7e6f6CCFe485a087F0F819eaBfDBfb1a49b97677'),
        # Master key is an L2 account with xtz balance to fund other accounts
        Variable(
            'L2_MASTER_KEY',
            default='8636c473b431be57109d4153735315a5cdf36b3841eb2cfa80b75b3dcd2d941a',
            is_secret=True,
        ),
        Variable('L2_RPC_URL', default='https://etherlink.dipdup.net'),
        Variable(
            'L2_ROLLUP_RPC_URL', default='https://etherlink-rollup-oxford.dipdup.net'
        ),
        Variable(
            'L2_KERNEL_ADDRESS', default='0x0000000000000000000000000000000000000000'
        ),
        Variable(
            'L2_WITHDRAW_PRECOMPILE_ADDRESS',
            default='0x0000000000000000000000000000000000000040',
        ),
    ]

    values = {variable.name: variable.ask() for variable in variables}

    with open('.env', 'w') as f:
        for name, value in values.items():
            f.write(f'{name}={value}\n')


load_dotenv()
