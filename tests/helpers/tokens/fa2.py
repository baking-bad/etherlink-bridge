from tests.helpers.contract import ContractHelper
from scripts.utility import DEFAULT_ADDRESS
from pytezos.client import PyTezosClient
from os.path import join
from os.path import dirname
from scripts.utility import pkh
from pytezos.contract.call import ContractCall


LedgerKey = tuple[str, int]


class FA2(ContractHelper):
    default_storage = {
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

    @classmethod
    def deploy(cls, client: PyTezosClient, balances: dict[LedgerKey, int]) -> 'FA2':
        """Deploys FA2 token with empty storage"""

        # TODO: move TOKENS_DIR to config / constants.py?
        tokens_dir = join(dirname(__file__), '..', '..', 'tokens')
        filename = join(tokens_dir, 'fa2-fxhash.tz')
        storage = cls.default_storage.copy()
        storage['ledger'] = balances
        # TODO: set token_metadata for all balances token_ids?
        storage['token_metadata'] = {0: (0, {})}

        return cls.deploy_from_file(filename, client, storage)

    def allow(self, operator: str, token_id: int = 0) -> ContractCall:
        return self.contract.update_operators([{
            'add_operator': {
                'owner': pkh(self.client),
                'operator': operator,
                'token_id': token_id,
            }
        }])

    # TODO: balance_of:
    # return self.contract.storage['ledger'][(address, token_id)]()

    # TODO: transfer(address_from, address_to, token_id, amount):
    '''
        self.fa2.contract.transfer([{
            'from_': address_from,
            'txs': [{
                'to_': address_to,
                'token_id': token_id,
                'amount': amount
            }]
        }]).send()
    '''