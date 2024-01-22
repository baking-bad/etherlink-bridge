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
            default='edsk2nu78mRwg4V5Ka7XCJFVbVPPwhry8YPeEHRwzGQHEpGAffDvrH',
            is_secret=True,
        ),
        # TODO: it is possible to get L1_PUBLIC_KEY_HASH from L1_PRIVATE_KEY
        Variable('L1_PUBLIC_KEY_HASH', default='tz1YG6P2GTQKFpd9jeuESam2vg6aA9HHRkKo'),
        Variable('L1_RPC_URL', default='https://rpc.tzkt.io/nairobinet/'),
        Variable('L1_ROLLUP_ADDRESS', default='sr1QgYF6ARMSLcWyAX4wFDrWFaZTyy4twbqe'),
        Variable(
            'L2_PRIVATE_KEY',
            default='8636c473b431be57109d4153735315a5cdf36b3841eb2cfa80b75b3dcd2d941a',
            is_secret=True,
        ),
        # TODO: it is possible to get L2_PUBLIC_KEY from L2_PRIVATE_KEY
        Variable('L2_PUBLIC_KEY', default='0xBefD2C6fFC36249ebEbd21d6DF6376ecF3BAc448'),
        # TODO: maybe it is better not to ask for L2_MASTER_KEY
        Variable(
            'L2_MASTER_KEY',
            default='9722f6cc9ff938e63f8ccb74c3daa6b45837e5c5e3835ac08c44c50ab5f39dc0',
            is_secret=True,
        ),
        Variable('L2_RPC_URL', default='https://etherlink.dipdup.net'),
        Variable(
            'L2_ROLLUP_RPC_URL', default='https://etherlink-rollup-nairobi.dipdup.net'
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
