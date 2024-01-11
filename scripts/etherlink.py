import click
import subprocess
from typing import (
    Optional,
    Any,
)
from scripts.environment import load_or_ask
from tezos.tests.helpers.utility import make_address_bytes
import requests


@click.command()
@click.option('--public-key', default=None, help='Etherlink address to fund.')
@click.option(
    '--sender-private-key',
    default=None,
    help='Use the provided private key to fund from.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def fund_account(
    public_key: Optional[str],
    sender_private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Funds given Etherlink address with 1 tez"""

    public_key = public_key or load_or_ask('L2_PUBLIC_KEY')
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    sender_private_key = sender_private_key or load_or_ask(
        'L2_MASTER_KEY', is_secret=True
    )

    result = subprocess.run(
        [
            'cast',
            'send',
            public_key,
            '--value',
            '1ether',
            '--private-key',
            sender_private_key,
            '--rpc-url',
            rpc_url,
            '--legacy',
        ],
        cwd='etherlink',
        # NOTE: not checking for return code, because it is very common
        # to get non-zero exit status
        # check=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stderr)
        return

    print('Successfully funded account:')
    print(result.stdout)


@click.command()
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticketer-content-bytes',
    required=True,
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. Use `get_ticket_params` function to get the correct value for a given ticket address.',
)
# TODO: consider extracting token name from the ticketer content bytes
@click.option(
    '--token-name', required=True, help='The name of the ERC20 token on Etherlink side.'
)
@click.option(
    '--token-symbol',
    required=True,
    help='The symbol of the ERC20 token on Etherlink side.',
)
@click.option(
    '--decimals',
    default=0,
    help='The number of decimals of the ERC20 token on Etherlink side.',
)
@click.option(
    '--kernel-address',
    default=None,
    help='The address of the Etherlink kernel which will be managing token.',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def deploy_erc20(
    ticketer_address_bytes: str,
    ticketer_content_bytes: str,
    token_name: str,
    token_symbol: str,
    decimals: int,
    kernel_address: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Deploys ERC20 Proxy contract with given parameters"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    kernel_address = kernel_address or load_or_ask('L2_KERNEL_ADDRESS')

    result = subprocess.run(
        [
            'forge',
            'create',
            '--legacy',
            '--rpc-url',
            rpc_url,
            '--private-key',
            private_key,
            'src/ERC20Proxy.sol:ERC20Proxy',
            '--constructor-args',
            ticketer_address_bytes,
            ticketer_content_bytes,
            kernel_address,
            token_name,
            token_symbol,
            '0',
            '--gas-limit',
            '200000',
        ],
        cwd='etherlink',
        # NOTE: not checking for return code, because it is very common
        # to get non-zero exit status
        # check=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stderr)
        return

    print('Successfully deployed ERC20 contract:')
    print(result.stdout)


@click.command()
@click.option(
    '--proxy-address',
    required=True,
    help='The address of the ERC20 proxy token contract which should burn token.',
)
@click.option(
    '--router-address',
    required=True,
    help='The address of the Router contract on the Tezos side (Ticketer address for FA2 and FA1.2 tokens).',
)
@click.option(
    '--amount', required=True, type=int, help='The amount of tokens to be withdrawn.'
)
@click.option(
    '--ticketer-address-bytes',
    required=True,
    help='The address of the ticketer contract encoded in forged form: `| 0x01 | 20 bytes | 0x00 |`. Use `get_ticketer_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--ticketer-content-bytes',
    required=True,
    help='The content of the ticket as micheline expression is in its forged form, **legacy optimized mode**. Use `get_ticket_params` function to get the correct value for a given ticket address.',
)
@click.option(
    '--receiver-address',
    default=None,
    help='The address of the receiver of the tokens in Tezos.',
)
@click.option(
    '--withdraw-precompile',
    default=None,
    help='The address of the withdraw precompile contract.',
)
@click.option('--private-key', default=None, help='Use the provided private key.')
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
def withdraw(
    proxy_address: str,
    router_address: str,
    amount: int,
    ticketer_address_bytes: str,
    ticketer_content_bytes: str,
    receiver_address: Optional[str],
    withdraw_precompile: Optional[str],
    private_key: Optional[str],
    rpc_url: Optional[str],
) -> None:
    """Withdraws token from L2 to L1"""

    private_key = private_key or load_or_ask('L2_PRIVATE_KEY', is_secret=True)
    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    withdraw_precompile = withdraw_precompile or load_or_ask(
        'L2_WITHDRAW_PRECOMPILE_ADDRESS'
    )

    receiver_address = receiver_address or load_or_ask('L1_PUBLIC_KEY_HASH')
    receiver_address_bytes = make_address_bytes(receiver_address)
    router_address_bytes = make_address_bytes(router_address)
    routing_info = receiver_address_bytes + router_address_bytes

    result = subprocess.run(
        [
            'cast',
            'send',
            withdraw_precompile,
            'withdraw(address,bytes,uint256,bytes22,bytes)',
            proxy_address,
            routing_info,
            str(amount),
            ticketer_address_bytes,
            ticketer_content_bytes,
            '--rpc-url',
            rpc_url,
            '--private-key',
            private_key,
            '--legacy',
            '--gas-limit',
            '300000',
        ],
        cwd='etherlink',
        # NOTE: not checking for return code, because it is very common
        # to get non-zero exit status
        # check=True,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stderr)
        return

    print('Successfully called withdraw:')
    print(result.stdout)


@click.command()
@click.option(
    '--tx-hash',
    required=True,
    help='The hash of the transaction which called withdraw function.',
)
@click.option('--rpc-url', default=None, help='Etherlink RPC URL.')
@click.option(
    '--kernel-address',
    default=None,
    help='The address of the Etherlink kernel which emits Withdrawal event.',
)
def parse_withdrawal_event(
    tx_hash: str, rpc_url: Optional[str], kernel_address: Optional[str]
) -> dict[str, Any]:
    """Parses the withdrawal event from the transaction receipt"""

    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    kernel_address = kernel_address or load_or_ask('L2_KERNEL_ADDRESS')

    result = requests.post(
        rpc_url,
        json={
            'jsonrpc': '2.0',
            'method': 'eth_getTransactionReceipt',
            'params': [tx_hash],
            'id': 1,
        },
    )

    if result.status_code != 200:
        print(result.text)
        return {'error': result.text}

    receipt = result.json()['result']

    if receipt is None:
        print('Transaction not found')
        return {'error': 'Transaction not found'}

    logs = receipt['logs']

    if len(logs) == 0:
        print('No logs found')
        return {'error': 'No logs found'}

    # NOTE: the order of logs is not determined, so we need to find the kernel log:
    kernel_logs = [log for log in logs if log['address'] == kernel_address]
    if len(kernel_logs) == 0:
        print('Kernel logs not found')
        return {'error': 'Kernel logs not found'}

    assert len(kernel_logs) == 1, 'Multiple kernel logs found'
    data = kernel_logs[0]['data']
    outbox_level = int(data[-128:-64], 16)
    outbox_index = int(data[-64:], 16)

    print(f'outbox_level: {outbox_level}')
    print(f'outbox_index: {outbox_index}')
    return {
        'outbox_level': outbox_level,
        'outbox_index': outbox_index,
    }
