"""Deposit statistics from the bridge indexer: totals, by token, by status."""

from collections import Counter

import click
from gql import gql

from scripts import cli_options
from scripts.monitoring.common import (
    make_client,
    print_breakdown,
    print_coverage,
    run_query,
)

QUERY = gql(
    """
    query Deposits($limit: Int!) {
        bridge_operation(
            where: {type: {_eq: "deposit"}}
            order_by: {created_at: desc}
            limit: $limit
        ) {
            status
            deposit { l1_transaction { ticket { token { symbol id } } } }
        }
        bridge_operation_aggregate(where: {type: {_eq: "deposit"}}) {
            aggregate { count }
        }
    }
    """
)


def deposit_token(operation: dict) -> str:
    """The token symbol of a deposit, or 'unknown' for cleared/failed routing."""

    deposit = operation.get('deposit') or {}
    l1_transaction = deposit.get('l1_transaction') or {}
    ticket = l1_transaction.get('ticket') or {}
    token = ticket.get('token') or {}
    # Fall back to the token id (address) when the symbol is not in the indexer
    # (e.g. freshly bootstrapped test tokens not yet known to the metadata service).
    return token.get('symbol') or token.get('id') or 'unknown'


limit_option = click.option(
    '--limit',
    default=1000,
    show_default=True,
    help='How many of the most recent deposits to sample (newest first).',
)


def monitor_deposits(limit: int) -> None:
    """Prints deposit stats from the active network's indexer (NETWORK env)."""

    client, url = make_client()
    click.echo(f'Indexer: {url}')

    data = run_query(client, QUERY, limit)
    operations = data['bridge_operation']
    total = data['bridge_operation_aggregate']['aggregate']['count']

    print_breakdown('Deposits by token', Counter(map(deposit_token, operations)))
    print_breakdown('Deposits by status', Counter(op['status'] for op in operations))
    print_coverage(len(operations), total, limit)


monitor_deposits_command = cli_options.command(
    monitor_deposits,
    name='monitor_deposits',
    options=[limit_option],
)
