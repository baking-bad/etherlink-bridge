from pytezos.client import PyTezosClient
from pytezos.rpc.query import RpcQuery
from dataclasses import dataclass, replace
from pytezos.operation.group import OperationGroup
from typing import Optional
from scripts.helpers.utility import to_micheline
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)
from scripts.helpers.ticket_content import TicketContent


def get_ticket_balance(
    client: PyTezosClient,
    owner: Addressable,
    ticketer: str,
    content: TicketContent,
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
        'content_type': to_micheline(content.michelson_type),
        'content': content.to_micheline(),
    }

    result = query._post(json=queried_ticket)  # type: ignore
    return int(result)


@dataclass
class Ticket:
    owner: Addressable
    ticketer: str
    content: TicketContent
    amount: int

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

        return cls(
            owner=owner,
            ticketer=ticketer,
            content=content,
            amount=get_ticket_balance(client, owner, ticketer, content),
        )

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
            ticket_contents=self.content.to_micheline(),
            ticket_ty=to_micheline(self.content.michelson_type),
            ticket_ticketer=self.ticketer,
            ticket_amount=self.amount,
            destination=get_address(destination),
            entrypoint=entrypoint,
        )
        return transfer_op


def deserialize_ticket(owner: Addressable, raw_ticket: dict) -> Ticket:
    expected_content_type = to_micheline(TicketContent.michelson_type)
    if expected_content_type != raw_ticket['content_type']:
        raise ValueError('Ticket content type does not match the given type')
    content = TicketContent.from_micheline(raw_ticket['content'])

    return Ticket(
        owner=owner,
        ticketer=raw_ticket['ticketer'],
        content=content,
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
