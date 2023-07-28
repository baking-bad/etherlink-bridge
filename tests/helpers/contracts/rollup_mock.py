from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import make_filename_from_build_name
from tests.helpers.tickets import (
    get_all_ticket_balances,
    Ticket,
)
from pytezos.operation.group import OperationGroup


class RollupMock(ContractHelper):
    default_storage = {
        'tickets': {},
        'messages': {},
        'next_id': 0,
    }

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Locker with empty storage"""

        filename = make_filename_from_build_name('rollup-mock')
        return cls.originate_from_file(filename, client, cls.default_storage)

    def get_tickets(self) -> list[Ticket]:
        """Returns list of tickets in storage"""

        return get_all_ticket_balances(self.client, self.address)
