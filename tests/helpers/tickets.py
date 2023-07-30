from pytezos.client import PyTezosClient
from pytezos.rpc.query import RpcQuery
from typing import TypedDict


class Ticket(TypedDict):
    ticketer: str
    content_type: dict
    content: dict
    amount: int


def deserialize_ticket(raw_ticket: dict) -> Ticket:
    return {
        'ticketer': raw_ticket['ticketer'],
        'content_type': raw_ticket['content_type'],
        'content': raw_ticket['content'],
        'amount': int(raw_ticket['amount']),
    }


# TODO: consider creating Account abstraction that have method get_tickets?
def get_all_ticket_balances(client: PyTezosClient, address: str) -> list[Ticket]:
    # TODO: this might be not the best / easiest way to make RPC call,
    # need to research more to find good way to do this:
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/all_ticket_balances',
        params=['main', last_block_hash, address]
    )

    result = query()
    return [deserialize_ticket(ticket) for ticket in result]


def get_all_ticket_balances_by_ticketer(
    client: PyTezosClient,
    address: str,
    ticketer: str,
) -> list[Ticket]:
    tickets = get_all_ticket_balances(client, address)
    return list(
        filter(
            lambda t: t['ticketer'] == ticketer,
            tickets
        )
    )


def get_ticket_balance(
    client: PyTezosClient,
    address: str,
    ticketer: str,
    content_type: dict,
    content: dict,
) -> int:
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/ticket_balance',
        params=['main', last_block_hash, address]
    )

    queried_ticket = {
        'ticketer': ticketer,
        'content_type': content_type,
        'content': content,
    }

    # TODO: looks like _post is not the best way to make RPC call
    result = query._post(json=queried_ticket)  # type: ignore
    return int(result)


def create_expected_ticket(
        ticketer: str,
        token_id: int,
        payload: str,
        amount: int = 0,
    ) -> Ticket:

    """ Creates ticket that can be created by Ticketer and RollupMock
        for given ticketer, token_id and amount """

    content_type = {
        'prim': 'pair',
        'args': [
            {'prim': 'nat'},
            {'prim': 'bytes'}
        ]
    }

    content = {
        'prim': 'Pair',
        'args': [
            {'int': str(token_id)},
            {'bytes': payload}
        ]
    }

    return {
        'ticketer': ticketer,
        'content_type': content_type,
        'content': content,
        'amount': amount,
    }
