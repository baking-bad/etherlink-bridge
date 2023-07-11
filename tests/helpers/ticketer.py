from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from scripts.utility import make_filename_from_build_name


class Ticketer(ContractHelper):
    default_storage = {
        'extra_metadata': {},
        'metadata': {},
        'token_ids': {},
        'next_token_id': 0,
    }

    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'Ticketer':
        """Deploys Ticketer with empty storage"""

        filename = make_filename_from_build_name('ticketer')
        return cls.deploy_from_file(filename, client, cls.default_storage)
