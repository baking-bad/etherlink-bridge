from tezos.tests.helpers.contracts.tokens.token import TokenHelper
from tezos.tests.helpers.utility import (
    DEFAULT_ADDRESS,
    pack,
    get_tokens_dir,
    originate_from_file,
)
from pytezos.client import PyTezosClient
from os.path import join
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup
from tezos.tests.helpers.metadata import Metadata
from tezos.tests.helpers.addressable import (
    Addressable,
    get_address,
)


FA12AsDictType = dict[str, str]
FA12AsTupleType = tuple[str, str]


class FA12(TokenHelper):
    default_storage = {
        'tokens': {},
        'allowances': {},
        'admin': DEFAULT_ADDRESS,
        'total_supply': 0,
        'metadata': Metadata.make(
            name='Test FA1.2 Token',
            description='Simple test FA1.2 token based on Ctez token from mainnet.',
        ),
        'token_metadata': {},
    }

    @classmethod
    def originate(
        cls, client: PyTezosClient, balances: dict[Addressable, int], token_id: int = 0
    ) -> OperationGroup:
        """Deploys FA1.2 token with provided balances in the storage"""

        filename = join(get_tokens_dir(), 'fa12-Ctez.tz')
        storage = cls.default_storage.copy()
        storage['tokens'] = {
            get_address(addressable): amount for addressable, amount
            in balances.items()
        }
        storage['token_metadata'] = {0: (0, {})}
        storage['total_supply'] = sum(balances.values())
        return originate_from_file(filename, client, storage)

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        return cls.originate(client, {})

    def allow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        # Allow makes approval for the total supply of the token
        return self.contract.approve(
            {
                'spender': get_address(operator),
                'value': self.contract.storage['total_supply'](),
            }
        )

    def disallow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        # Revoke allowance
        return self.contract.approve(
            {
                'spender': get_address(operator),
                'value': 0,
            }
        )

    def as_dict(self) -> FA12AsDictType:
        return {'fa12': self.address}

    def as_tuple(self) -> FA12AsTupleType:
        return ('fa12', self.address)

    def get_balance(
        self,
        client_or_contract: Addressable,
    ) -> int:
        """Returns balance of given address.
        NOTE: this is the implementation only works with Ctez token.
        TODO: consider make special implementations for different FA1.2 tokens.
        """

        address = get_address(client_or_contract)
        try:
            balance = self.contract.storage['tokens'][address]()
        except KeyError:
            balance = 0
        assert isinstance(balance, int)
        return balance

    def make_token_info(self) -> dict[str, bytes]:
        return {
            'contract_address': pack(self.address, 'address'),
            'token_type': pack("FA1.2", 'string'),
        }
