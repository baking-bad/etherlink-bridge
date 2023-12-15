from tests.helpers.contracts.tokens.token import (
    TokenHelper,
    FA12AsDictType,
    FA12AsTupleType,
)
from tests.helpers.utility import (
    DEFAULT_ADDRESS,
    pkh,
    pack,
)
from pytezos.client import PyTezosClient
from os.path import join
from os.path import dirname
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup
from tests.helpers.metadata import make_metadata


class FA12(TokenHelper):
    default_storage = {
        'tokens': {},
        'allowances': {},
        'admin': DEFAULT_ADDRESS,
        'total_supply': 0,
        'metadata': make_metadata(
            template=dict(
                name='Test FA1.2 Token',
                description='Simple test FA1.2 token based on Ctez token from mainnet.',
            ),
        ),
        'token_metadata': {},
    }

    @classmethod
    def originate(
        cls, client: PyTezosClient, balances: dict[str, int]
    ) -> OperationGroup:
        """Deploys FA1.2 token with provided balances in the storage"""

        # TODO: move TOKENS_DIR to config / constants.py? [2]
        tokens_dir = join(dirname(__file__), '..', '..', '..', 'tokens')
        filename = join(tokens_dir, 'fa12-Ctez.tz')
        storage = cls.default_storage.copy()
        storage['tokens'] = {address: amount for address, amount in balances.items()}
        storage['token_metadata'] = {0: (0, {})}
        storage['total_supply'] = sum(balances.values())
        return cls.originate_from_file(filename, client, storage)

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        return cls.originate(client, {})

    def allow(self, operator: str) -> ContractCall:
        # Allow makes approval for the total supply of the token
        return self.contract.approve(
            {
                'spender': operator,
                'value': self.contract.storage['total_supply'](),
            }
        )

    def as_dict(self) -> FA12AsDictType:
        return {'fa12': self.address}

    def as_tuple(self) -> FA12AsTupleType:
        return ('fa12', self.address)

    def get_balance(self, address: str) -> int:
        balance = self.contract.storage['tokens'][address]()
        # TODO: return default 0 balance if no record in ledger? [2]
        assert isinstance(balance, int)
        return balance

    def make_token_info(self) -> dict[str, bytes]:
        return {
            'contract_address': pack(self.address, 'address'),
            'token_type': pack("FA1.2", 'string'),
        }
