from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from scripts.utility import make_filename_from_build_name

class Locker(ContractHelper):
    default_storage = []

    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'Locker':
        """Deploys Locker with empty storage"""

        filename = make_filename_from_build_name('locker')
        return cls.deploy_from_file(filename, client, cls.default_storage)

    def get_tickets(self) -> list:
        """Returns list of tickets in storage"""

        return self.contract.storage()
