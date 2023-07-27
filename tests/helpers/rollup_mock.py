from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.utility import make_filename_from_build_name
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

    # TODO: consider improving this generic list type
    def get_tickets(self) -> list:
        """Returns list of tickets in storage"""

        # TODO: use RPC call to all_ticket_balances endpoint instead
        raise NotImplementedError
        # return self.contract.storage['tickets']()  # type: ignore
