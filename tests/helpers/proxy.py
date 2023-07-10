from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from scripts.utility import DEFAULT_ADDRESS
from scripts.utility import make_filename_from_build_name


class Proxy(ContractHelper):
    storage = {
        'data': DEFAULT_ADDRESS,
        'receiver': DEFAULT_ADDRESS,
    }

    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'Proxy':
        """Deploys Proxy with empty storage"""

        filename = make_filename_from_build_name('proxy')
        return cls.deploy_from_file(filename, client, cls.storage)
