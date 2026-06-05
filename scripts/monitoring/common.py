"""Shared helpers for the bridge monitoring scripts.

Both scripts read the indexer URL from the active network config (`NETWORK` env),
sample the most recent N `bridge_operation` rows, and print client-side breakdowns
as accented tables — the same look as the other CLI tools.
"""

from collections import Counter
from typing import Any

import click
from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from graphql import DocumentNode
from tabulate import tabulate

from scripts.helpers.formatting import accent
from scripts.networks import load_network


def make_client() -> tuple[Client, str]:
    """GraphQL client for the active network's bridge indexer."""

    url = load_network().network.indexer_graphql_url
    transport = RequestsHTTPTransport(url=url)
    return Client(transport=transport), url


def run_query(client: Client, query: DocumentNode, limit: int) -> dict[str, Any]:
    with client as session:
        result: dict[str, Any] = session.execute(
            query, variable_values={'limit': limit}
        )
        return result


def print_breakdown(title: str, counter: Counter) -> None:
    """Prints a `label -> count` breakdown as a table, busiest first."""

    rows = sorted(counter.items(), key=lambda item: item[1], reverse=True)
    rows.append(('TOTAL', sum(counter.values())))
    click.echo()
    click.echo(accent(title))
    click.echo(tabulate(rows, headers=['', 'count'], tablefmt='simple'))


def print_coverage(fetched: int, total: int, limit: int) -> None:
    """Notes how much of the indexer the sample covers (the rest is older)."""

    click.echo()
    if total > fetched:
        click.echo(
            accent(f'Sampled the {fetched} most recent of {total} total. ')
            + f'Raise --limit (now {limit}) to include older operations.'
        )
    else:
        click.echo(f'Covered all {total} operations.')
