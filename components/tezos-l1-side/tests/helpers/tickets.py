from pytezos.client import PyTezosClient
from pytezos.rpc.query import RpcQuery
from typing import TypedDict
from tests.helpers.contracts.tokens.token import TokenHelper
from tests.helpers.utility import (
    to_michelson_type,
    pack,
)


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
    ticket: Ticket,
    address: str,
) -> int:
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/ticket_balance',
        params=['main', last_block_hash, address]
    )

    queried_ticket = {
        'ticketer': ticket['ticketer'],
        'content_type': ticket['content_type'],
        'content': ticket['content'],
    }

    # TODO: looks like _post is not the best way to make RPC call
    result = query._post(json=queried_ticket)  # type: ignore
    return int(result)


# TODO: consider moving this function to the Ticketer and RollupMock helpers?
#       (maybe create some intermediate class that supports this logic)
def create_ticket(
        ticketer: str,
        token_id: int,
        token_info: dict[str, bytes],
        amount: int = 0,
    ) -> Ticket:

    """ Creates ticket that can be created by Ticketer and RollupMock
        for given ticketer, token_id and amount
        ticketer: address of the ticketer contract
        token_id: id of the ticket inside ticketer contract
        token: L1 token used to create ticket payload
    """

    content_type = {
        'prim': 'pair',
        'args': [
            {'prim': 'nat'},
            {'prim': 'option',
                'args': [
                    {'prim': 'bytes'}
                ],
            },
        ],
    }

    # TODO: consider moving this to some consts file? [2], another in token.py
    MAP_TOKEN_INFO_TYPE = 'map %token_info string bytes'
    ticket_contents = {
        'token_id': token_id,
        'token_info': pack(token_info, MAP_TOKEN_INFO_TYPE),
    }

    content = to_michelson_type(
        ticket_contents,
        # TODO: this ticket type expression is duplicated, consider
        #      moving it to some common place (?)
        'pair (nat %token_id) (option %token_info bytes)',
    ).to_micheline_value()

    return {
        'ticketer': ticketer,
        'content_type': content_type,
        'content': content,
        'amount': amount,
    }
