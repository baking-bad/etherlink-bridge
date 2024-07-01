import click
from typing import (
    Optional,
    Any,
)
from scripts.environment import load_or_ask
import requests


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
    help='The address of the Etherlink kernel that emits Withdrawal event.',
)
def parse_withdrawal_event(
    tx_hash: str, rpc_url: Optional[str], kernel_address: Optional[str]
) -> dict[str, Any]:
    """Parses the withdrawal event from the transaction receipt"""

    rpc_url = rpc_url or load_or_ask('L2_RPC_URL')
    kernel_address = kernel_address or load_or_ask('L2_KERNEL_ADDRESS')

    # TODO: replace this logic with web3.py
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
