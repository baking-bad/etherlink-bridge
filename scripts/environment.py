from dotenv import load_dotenv
from getpass import getpass
import os
import click
from dataclasses import dataclass
from web3 import Web3
from eth_account.signers.local import LocalAccount
from pytezos.client import PyTezosClient
from pytezos import pytezos
from typing import Optional


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
        Variable('L1_RPC_URL', default='https://rpc.tzkt.io/parisnet/'),
        Variable('L1_ROLLUP_ADDRESS', default='sr1D7sVcMMUMUHUK5hxcowgLtyUa9HnFnrEs'),
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
            'L2_ROLLUP_RPC_URL', default='https://etherlink-rollup-paris.dipdup.net'
        ),
        Variable(
            'L2_KERNEL_ADDRESS', default='0x0000000000000000000000000000000000000000'
        ),
        Variable(
            'L2_WITHDRAW_PRECOMPILE_ADDRESS',
            default='0xff00000000000000000000000000000000000002',
        ),
    ]

    values = {variable.name: variable.ask() for variable in variables}

    with open('.env', 'w') as f:
        for name, value in values.items():
            f.write(f'{name}={value}\n')


def get_tezos_client(shell: Optional[str], key: Optional[str]) -> PyTezosClient:
    """Returns client with private key and rpc url set in environment variables"""

    key = key or load_or_ask('L1_PRIVATE_KEY', is_secret=True)
    shell = shell or load_or_ask('L1_RPC_URL')
    client: PyTezosClient = pytezos.using(shell=shell, key=key)
    return client


def get_etherlink_web3(shell: Optional[str]) -> Web3:
    """Returns Web3 client with rpc url set in environment variables"""

    shell = shell or load_or_ask('L2_RPC_URL')
    web3 = Web3(Web3.HTTPProvider(shell))

    if not web3.is_connected():
        raise Exception(f'Failed to connect to Etherlink node: {shell}')

    return web3


def get_etherlink_account(
    web3: Optional[Web3], private_key: Optional[str]
) -> LocalAccount:
    """Returns Account with private key set in environment variables"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY', is_secret=True)
    if web3 is None:
        web3 = get_etherlink_web3(None)
    account: LocalAccount = web3.eth.account.from_key(private_key)
    return account


load_dotenv()
