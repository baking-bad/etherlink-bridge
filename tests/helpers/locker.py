from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.utility import make_filename_from_build_name
from pytezos.operation.group import OperationGroup


class Locker(ContractHelper):
    default_storage = []

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Locker with empty storage"""

        filename = make_filename_from_build_name('locker')
        return cls.originate_from_file(filename, client, cls.default_storage)

    # TODO: consider improving this generic list type
    def get_tickets(self) -> list:
        """Returns list of tickets in storage"""

        return self.contract.storage()  # type: ignore
