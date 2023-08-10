from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import get_build_dir
from tests.helpers.tickets import (
    get_all_ticket_balances,
    Ticket,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from os.path import join


class RollupMock(ContractHelper):
    default_storage = {
        'tickets': {},
        'messages': {},
        'next_message_id': 0,
        'next_l2_id': 0,
        'l2_ids': {},
        'ticket_ids': {},
    }

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Locker with empty storage"""

        filename = join(get_build_dir(), 'rollup-mock.tz')
        return cls.originate_from_file(filename, client, cls.default_storage)

    def get_tickets(self) -> list[Ticket]:
        """Returns list of tickets in storage"""

        return get_all_ticket_balances(self.client, self.address)

    def get_message(self, message_id: int = 0) -> dict:
        """Returns message from storage with given id"""

        message = self.contract.storage['messages'][message_id]()
        assert type(message) is dict
        return message

    def l1_release(self, message_id: int = 0) -> ContractCall:
        """Releases message with given id"""

        return self.contract.l1_release(message_id)
