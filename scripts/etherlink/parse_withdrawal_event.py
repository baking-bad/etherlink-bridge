import click
from typing import (
    Any,
)
import requests
from scripts import cli_options


@click.command()
@click.option(
    '--tx-hash',
    required=True,
    prompt='Transaction hash',
    help='The hash of the transaction which called withdraw function.',
)
@cli_options.etherlink_rpc_url
@cli_options.kernel_address
def parse_withdrawal_event(
    tx_hash: str, etherlink_rpc_url: str, kernel_address: str
) -> dict[str, Any]:
    """Parses the withdrawal event from the transaction receipt"""

    # TODO: replace this logic with web3.py, there should be a way to parse events
    result = requests.post(
        etherlink_rpc_url,
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
        click.echo('No logs found')
        raise click.Abort()

    # NOTE: the order of logs is not determined, so we need to find the kernel log:
    kernel_logs = [log for log in logs if log['address'] == kernel_address]
    if len(kernel_logs) == 0:
        click.echo('There are logs, but no kernel logs found')
        raise click.Abort()

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
