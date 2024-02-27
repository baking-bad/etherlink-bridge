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
from tezos.tests.helpers.addressable import (
    Addressable,
    get_address,
)


# Ticket content type is fixed to match FA2.1 ticket content type:
TICKET_CONTENT_TYPE = '(pair nat (option bytes))'


@dataclass
class TicketContent:
    token_id: int
    token_info: Optional[dict]


def get_ticket_balance(
    client,
    owner: Addressable,
    ticketer: str,
    content_type: dict,
    content: dict,
) -> int:

    owner_address = get_address(owner)
    last_block_hash = client.shell.head.hash()
    query = RpcQuery(
        node=client.shell.node,
        path='/chains/{}/blocks/{}/context/contracts/{}/ticket_balance',
        params=['main', last_block_hash, owner_address],
    )

    queried_ticket = {
        'ticketer': ticketer,
        'content_type': content_type,
        'content': content,
    }

    result = query._post(json=queried_ticket)  # type: ignore
    return int(result)


@dataclass
class Ticket:
    owner: Addressable
    ticketer: str
    content_type: dict
    content: dict
    amount: int

    @staticmethod
    def make_content_micheline(content_object: TicketContent) -> dict:
        return to_michelson_type(
            (content_object.token_id, content_object.token_info),
            TICKET_CONTENT_TYPE,
        ).to_micheline_value()

    @classmethod
    def create(
        cls,
        client: PyTezosClient,
        owner: Addressable,
        ticketer: str,
        content: TicketContent,
    ) -> 'Ticket':
        """Special helper to create a ticket with TZIP-29 ticket content type
        from provided TicketContent object and given owner and ticketer
        addresses. Requires a client to get ticket balance"""

        content_type = to_micheline(TICKET_CONTENT_TYPE)
        content_micheline = cls.make_content_micheline(content)
        amount = get_ticket_balance(
            client, owner, ticketer, content_type, content_micheline
        )

        return cls(
            owner=owner,
            ticketer=ticketer,
            content_type=content_type,
            content=content_micheline,
            amount=amount
        )

    def make_bytes_payload(self) -> str:
        """This function allows to make ticket payload bytes to be used in
        L2 Etherlink Bridge contracts"""

        michelson_type = MichelsonType.match(self.content_type)
        value = michelson_type.from_micheline_value(self.content)
        payload: str = value.forge('legacy_optimized').hex()
        return payload

    def split(self, amount: int) -> tuple['Ticket', 'Ticket']:
        """Splits the ticket into two tickets with given amounts"""

        if amount > self.amount:
            raise ValueError('Amount to split is greater than ticket amount')

        ticket1 = replace(self, amount=amount)
        ticket2 = replace(self, amount=self.amount - amount)
        return ticket1, ticket2

    def transfer(
        self,
        destination: Addressable,
        entrypoint: Optional[str] = None,
    ) -> OperationGroup:
        """Transfers given amount of tickets to given address.
        If amount is not provided, then it will transfer all tickets."""

        entrypoint = entrypoint or 'default'
        if isinstance(self.owner, PyTezosClient):
            client = self.owner
        else:
            raise ValueError('Transfer ticket owner should be a client')

        transfer_op: OperationGroup = client.transfer_ticket(
            ticket_contents=self.content,
            ticket_ty=self.content_type,
            ticket_ticketer=self.ticketer,
            ticket_amount=self.amount,
            destination=get_address(destination),
            entrypoint=entrypoint,
        )
        return transfer_op


def deserialize_ticket(owner: Addressable, raw_ticket: dict) -> Ticket:
    return Ticket(
        owner=owner,
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
