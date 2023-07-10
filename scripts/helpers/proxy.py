from scripts.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient


# Default address used as a placeholder for the receiver
BURN_ADDRESS = 'tz1burnburnburnburnburnburnburjAYjjX'


class Proxy(ContractHelper):
    storage = {
        'data': BURN_ADDRESS,
        'receiver': BURN_ADDRESS,
    }

    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'Proxy':
        """Deploys Proxy with empty storage"""

        return cls.deploy_from_build('proxy', client, cls.storage)
