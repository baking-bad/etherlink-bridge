from pytezos.client import PyTezosClient
from pytezos.rpc.query import RpcQuery
from typing import TypedDict

from pytezos.michelson.types.base import MichelsonType


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


def get_all_ticket_balances(client: PyTezosClient, address: str) -> list[Ticket]:
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/all_ticket_balances',
        params=['main', last_block_hash, address],
    )

    result = query()
    return [deserialize_ticket(ticket) for ticket in result]


def get_all_ticket_balances_by_ticketer(
    client: PyTezosClient,
    address: str,
    ticketer: str,
) -> list[Ticket]:
    tickets = get_all_ticket_balances(client, address)
    return list(filter(lambda t: t['ticketer'] == ticketer, tickets))


def get_ticket_balance(
    client: PyTezosClient,
    ticket: Ticket,
    address: str,
) -> int:
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/ticket_balance',
        params=['main', last_block_hash, address],
    )

    queried_ticket = {
        'ticketer': ticket['ticketer'],
        'content_type': ticket['content_type'],
        'content': ticket['content'],
    }

    result = query._post(json=queried_ticket)  # type: ignore
    return int(result)


def make_ticket_payload_bytes(ticket: Ticket) -> str:
    """This function allows to make ticket payload bytes to be used in
    L2 Etherlink Bridge contracts"""

    michelson_type = MichelsonType.match(ticket['content_type'])
    value = michelson_type.from_micheline_value(ticket['content'])
    payload: str = value.forge('legacy_optimized').hex()
    return payload
