from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)
from scripts.helpers.utility import (
    DEFAULT_ADDRESS,
    originate_from_file,
)
from os.path import (
    join,
    dirname,
)
from scripts.helpers.metadata import Metadata
from scripts.helpers.contracts.tokens.fa12.fa12 import FA12


class CtezToken(FA12):
    default_storage = {
        'ledger': {},
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
        cls,
        client: PyTezosClient,
        balances: dict[Addressable, int],
        token_id: int = 0,
        token_info: dict | None = None,
    ) -> OperationGroup:
        """Deploys FA1.2 token with provided balances in the storage"""

        filename = join(dirname(__file__), 'Ctez.tz')
        storage = cls.default_storage.copy()
        storage['ledger'] = {
            get_address(addressable): amount for addressable, amount in balances.items()
        }
        if token_info is None:
            token_info = {}
        storage['token_metadata'] = {token_id: (token_id, token_info)}
        storage['total_supply'] = sum(balances.values())
        return originate_from_file(filename, client, storage)

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
            balance = self.contract.storage['ledger'][address]()
        except KeyError:
            balance = 0
        assert isinstance(balance, int)
        return balance
