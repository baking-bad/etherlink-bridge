from scripts.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient


class Ticketer(ContractHelper):
    storage = {
        'extra_metadata': {},
        'metadata': {},
        'token_ids': {},
        'next_token_id': 0,
    }

    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'Ticketer':
        """Deploys Ticketer with empty storage"""

        return cls.deploy_from_build('ticketer', client, cls.storage)
