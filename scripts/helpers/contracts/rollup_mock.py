from scripts.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from scripts.helpers.utility import (
    get_build_dir,
    originate_from_file,
)
from scripts.helpers.ticket import (
    Ticket,
    get_all_tickets,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from os.path import join
from scripts.helpers.metadata import Metadata
from typing import (
    TypedDict,
    Any,
)
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)
from scripts.helpers.contracts.ticketer import Ticketer


class TicketId(TypedDict):
    token_id: int
    ticketer: Ticketer


class ExecuteParams(TypedDict):
    ticket_id: TicketId
    amount: int
    receiver: Addressable
    router: Addressable


def serialize_ticket_id(ticket_id: TicketId) -> dict[str, Any]:
    return {
        'token_id': ticket_id['token_id'],
        'ticketer': ticket_id['ticketer'].address,
    }


def serialize_execute_params(params: ExecuteParams) -> dict[str, Any]:
    return {
        'ticket_id': serialize_ticket_id(params['ticket_id']),
        'amount': params['amount'],
        'receiver': get_address(params['receiver']),
        'router': get_address(params['router']),
    }


class RollupMock(ContractHelper):
    @classmethod
    def originate(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Locker with empty storage"""

        storage = {
            'tickets': {},
            'metadata': Metadata.make_default(
                name='Rollup Mock',
                description='The Rollup Mock is a component of the Bridge Protocol Prototype, designed to emulate the operations of a real smart rollup on L1 side.',
            ),
        }

        filename = join(get_build_dir(), 'rollup-mock.tz')
        return originate_from_file(filename, client, storage)

    def get_tickets(self) -> list[Ticket]:
        """Returns list of tickets in storage"""

        return get_all_tickets(self.client, self.address)

    def execute_outbox_message(self, params: ExecuteParams) -> ContractCall:
        """Releases message with given id"""

        return self.contract.execute_outbox_message(serialize_execute_params(params))
