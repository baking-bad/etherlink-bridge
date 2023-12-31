from tests.helpers.contracts.tokens.token import (
    TokenHelper,
    FA2AsDictType,
    FA2AsTupleType,
)
from tests.helpers.utility import (
    DEFAULT_ADDRESS,
    pkh,
    pack,
    get_tokens_dir,
)
from pytezos.client import PyTezosClient
from os.path import join
from os.path import dirname
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup
from tests.helpers.metadata import Metadata


class FA2(TokenHelper):
    default_storage = {
        'administrator': DEFAULT_ADDRESS,
        'all_tokens': 0,
        'issuer': DEFAULT_ADDRESS,
        'ledger': {},
        'metadata': Metadata.make(
            name='Test FA2 Token',
            description='Simple test FA2 token based on fxhash token from mainnet.',
        ),
        'operators': {},
        'paused': False,
        'signer': DEFAULT_ADDRESS,
        'token_data': {},
        'token_metadata': {},
        'treasury_address': DEFAULT_ADDRESS,
    }
    token_id = 0

    @classmethod
    def originate(
        cls, client: PyTezosClient, balances: dict[str, int], token_id: int = 0
    ) -> OperationGroup:
        """Deploys FA2 token with provided balances in the storage"""

        filename = join(get_tokens_dir(), 'fa2-fxhash.tz')
        storage = cls.default_storage.copy()
        storage['ledger'] = {
            (address, token_id): amount for address, amount in balances.items()
        }
        storage['token_metadata'] = {token_id: (token_id, {})}
        cls.token_id = token_id
        return cls.originate_from_file(filename, client, storage)

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        return cls.originate(client, {})

    def allow(self, owner: str, operator: str) -> ContractCall:
        return self.contract.update_operators(
            [
                {
                    'add_operator': {
                        'owner': owner,
                        'operator': operator,
                        'token_id': self.token_id,
                    }
                }
            ]
        )

    def as_dict(self) -> FA2AsDictType:
        return {'fa2': (self.address, self.token_id)}

    def as_tuple(self) -> FA2AsTupleType:
        return ('fa2', (self.address, self.token_id))

    def get_balance(self, address: str) -> int:
        key = (address, self.token_id)
        balance = self.contract.storage['ledger'][key]()  # type: ignore
        assert isinstance(balance, int)
        return balance

    def make_token_info(self) -> dict[str, bytes]:
        return {
            'contract_address': pack(self.address, 'address'),
            'token_type': pack("FA2", 'string'),
            'token_id': pack(self.token_id, 'nat'),
        }

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
