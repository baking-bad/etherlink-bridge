from tests.helpers.contract import ContractHelper
from scripts.utility import DEFAULT_ADDRESS
from pytezos.client import PyTezosClient
from os.path import join
from os.path import dirname


class FA2(ContractHelper):
    storage = {
        'administrator': DEFAULT_ADDRESS,
        'all_tokens': 0,
        'issuer': DEFAULT_ADDRESS,
        'ledger': {},
        'metadata': {},
        'operators': {},
        'paused': False,
        'signer': DEFAULT_ADDRESS,
        'token_data': {},
        'token_metadata': {},
        'treasury_address': DEFAULT_ADDRESS,
    }

    # TODO: instead of deploy_default need to deploy with some tokens for addresses
    @classmethod
    def deploy_default(cls, client: PyTezosClient) -> 'FA2':
        """Deploys FA2 token with empty storage"""

        # TODO: move TOKENS_DIR to config?
        tokens_dir = join(dirname(__file__), '..', '..', 'tokens')
        filename = join(tokens_dir, 'fa2-fxhash.tz')
        return cls.deploy_from_file(filename, client, cls.storage)
