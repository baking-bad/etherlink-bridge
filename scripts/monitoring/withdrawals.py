"""Withdrawal statistics from the bridge indexer: totals, by token, by status,
and by kind (regular vs the fast-withdrawal variants)."""

from collections import Counter

import click
from gql import gql

from scripts.monitoring.common import (
    make_client,
    print_breakdown,
    print_coverage,
    run_query,
)

# bridge_operation.kind for withdrawals; null means a regular (slow) withdrawal.
KIND_LABELS = {
    None: 'regular',
    'fast_withdrawal': 'fast (user)',
    'fast_withdrawal_service_provider': 'fast (service provider)',
    'fast_withdrawal_payed_out': 'fast (claimed / paid out)',
}

QUERY = gql(
    """
    query Withdrawals($limit: Int!) {
        bridge_operation(
            where: {type: {_eq: "withdrawal"}}
            order_by: {created_at: desc}
            limit: $limit
        ) {
            status
            kind
            withdrawal { l2_transaction { ticket { token { symbol id } } } }
        }
        bridge_operation_aggregate(where: {type: {_eq: "withdrawal"}}) {
            aggregate { count }
        }
    }
    """
)


def withdrawal_token(operation: dict) -> str:
    """The token symbol of a withdrawal, or 'unknown' if not resolved yet.

    Resolved via the L1 ticket's token: the L2 `l2_token` symbol is often null for
    FA tokens, while the Tezos-side token carries the symbol.
    """

    withdrawal = operation.get('withdrawal') or {}
    l2_transaction = withdrawal.get('l2_transaction') or {}
    ticket = l2_transaction.get('ticket') or {}
    token = ticket.get('token') or {}
    # Fall back to the token id (address) when the symbol is not in the indexer.
    return token.get('symbol') or token.get('id') or 'unknown'


def withdrawal_kind(operation: dict) -> str:
    kind = operation.get('kind')
    return KIND_LABELS.get(kind, kind or 'regular')


@click.command()
@click.option(
    '--limit',
    default=1000,
    show_default=True,
    help='How many of the most recent withdrawals to sample (newest first).',
)
def monitor_withdrawals(limit: int) -> None:
    """Prints withdrawal stats from the active network's indexer (NETWORK env)."""

    client, url = make_client()
    click.echo(f'Indexer: {url}')

    data = run_query(client, QUERY, limit)
    operations = data['bridge_operation']
    total = data['bridge_operation_aggregate']['aggregate']['count']

    print_breakdown('Withdrawals by token', Counter(map(withdrawal_token, operations)))
    print_breakdown('Withdrawals by status', Counter(op['status'] for op in operations))
    print_breakdown('Withdrawals by kind', Counter(map(withdrawal_kind, operations)))
    print_coverage(len(operations), total, limit)
