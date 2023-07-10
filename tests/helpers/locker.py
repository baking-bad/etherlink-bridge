from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient


# Default address used as a placeholder for the receiver
BURN_ADDRESS = 'tz1burnburnburnburnburnburnburjAYjjX'


class Locker(ContractHelper):
    storage = []

    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'Locker':
        """Deploys Locker with empty storage"""

        return cls.deploy_from_build('locker', client, cls.storage)
