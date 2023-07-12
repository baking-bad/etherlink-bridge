from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from scripts.utility import make_filename_from_build_name
from pytezos.contract.call import ContractCall
from tests.helpers.tokens.token import TokenHelper


class Ticketer(ContractHelper):
    default_storage = {
        'extra_metadata': {},
        'metadata': {},
        'token_ids': {},
        'tokens': {},
        'next_token_id': 0,
    }

    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'Ticketer':
        """Deploys Ticketer with empty storage"""

        filename = make_filename_from_build_name('ticketer')
        return cls.deploy_from_file(filename, client, cls.default_storage)

    def deposit(self, token: TokenHelper, amount: int) -> ContractCall:
        params = (token.as_dict(), amount)
        return self.contract.deposit(params)
