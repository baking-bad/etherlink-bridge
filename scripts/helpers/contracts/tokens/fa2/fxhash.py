from os.path import (
    join,
    dirname,
)
from scripts.helpers.metadata import Metadata
from scripts.helpers.utility import DEFAULT_ADDRESS
from scripts.helpers.utility import originate_from_file
from scripts.helpers.contracts.tokens.fa2.fa2 import FA2
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)


class FxhashToken(FA2):
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

    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
        balances: dict[Addressable, int],
        token_id: int = 0,
        token_info: dict | None = None,
    ) -> OperationGroup:
        """Deploys FA2 token with provided balances in the storage"""

        filename = join(dirname(__file__), 'fxhash.tz')
        storage = cls.default_storage.copy()
        storage['ledger'] = {
            (get_address(addressable), token_id): amount
            for addressable, amount in balances.items()
        }
        if token_info is None:
            token_info = {}
        storage['token_metadata'] = {token_id: (token_id, token_info)}
        return originate_from_file(filename, client, storage)
