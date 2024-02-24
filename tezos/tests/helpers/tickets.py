from pytezos.client import PyTezosClient
from pytezos.rpc.query import RpcQuery
from dataclasses import dataclass, replace
from pytezos.operation.group import OperationGroup
from pytezos.michelson.types.base import MichelsonType
from typing import Optional
from tezos.tests.helpers.utility import (
    to_michelson_type,
    to_micheline,
)


# Ticket content type is fixed to match FA2.1 ticket content type:
TICKET_CONTENT_TYPE = '(pair nat (option bytes))'


@dataclass
class Ticket:
    client: PyTezosClient
    ticketer: str
    content_type: dict
    content: dict
    amount: int

    @classmethod
    def create(
        cls,
        client: PyTezosClient,
        ticketer: str,
        content_object: dict,
        content_type_michelson: str = TICKET_CONTENT_TYPE,
        amount: int = 0,
    ) -> 'Ticket':
        """Special helper to create a ticket with given content provided
        as a python object and content type provided as a michelson type
        """

        content = to_michelson_type(
            content_object,
            content_type_michelson,
        ).to_micheline_value()

        return cls(
            client=client,
            ticketer=ticketer,
            content_type=to_micheline(content_type_michelson),
            content=content,
            amount=amount,
        )

    def get_balance(self, address: str) -> int:
        last_block_hash = self.client.shell.head.hash()
        query = RpcQuery(
            node=self.client.shell.node,
            path='/chains/{}/blocks/{}/context/contracts/{}/ticket_balance',
            params=['main', last_block_hash, address],
        )

        queried_ticket = {
            'ticketer': self.ticketer,
            'content_type': self.content_type,
            'content': self.content,
        }

        result = query._post(json=queried_ticket)  # type: ignore
        return int(result)

    def make_bytes_payload(self) -> str:
        """This function allows to make ticket payload bytes to be used in
        L2 Etherlink Bridge contracts"""

        michelson_type = MichelsonType.match(self.content_type)
        value = michelson_type.from_micheline_value(self.content)
        payload: str = value.forge('legacy_optimized').hex()
        return payload

    def transfer(
        self,
        destination: str,
        amount: int,
    ) -> OperationGroup:
        """Transfers given amount of tickets to given address"""

        address_to = destination.split('%')[0]
        entrypoint = ''.join(destination.split('%')[1:])

        transfer_op: OperationGroup = self.client.transfer_ticket(
            ticket_contents=self.content,
            ticket_ty=self.content_type,
            ticket_ticketer=self.ticketer,
            ticket_amount=amount,
            destination=address_to,
            entrypoint=entrypoint,
        )
        return transfer_op

    def using(self, client: PyTezosClient) -> 'Ticket':
        """Returns new Ticket with updated client"""
        return replace(self, client=client)


def deserialize_ticket(client: PyTezosClient, raw_ticket: dict) -> Ticket:
    return Ticket(
        client=client,
        ticketer=raw_ticket['ticketer'],
        content_type=raw_ticket['content_type'],
        content=raw_ticket['content'],
        amount=int(raw_ticket['amount']),
    )


def get_all_tickets(
    client: PyTezosClient, address: Optional[str] = None
) -> list[Ticket]:
    """Returns all tickets of given address"""

    address = address or client.key.public_key_hash()
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/all_ticket_balances',
        params=['main', last_block_hash, address],
    )
    result = query()

    return [deserialize_ticket(client, raw_ticket) for raw_ticket in result]


def get_all_by_ticketer(
    client: PyTezosClient,
    address: str,
    ticketer: str,
) -> list[Ticket]:
    """Returns all tickets of given address created by given ticketer"""

    tickets = get_all_tickets(client, address)

    def filter_by_ticketer(ticket: Ticket) -> bool:
        return ticket.ticketer == ticketer

    return list(filter(filter_by_ticketer, tickets))
