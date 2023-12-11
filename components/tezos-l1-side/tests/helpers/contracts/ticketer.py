from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import (
    get_build_dir,
    to_michelson_type,
    to_micheline,
    pack,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from tests.helpers.contracts.tokens.token import TokenHelper
from typing import (
    Any,
    TypedDict,
)
from os.path import join
from tests.helpers.metadata import make_metadata


class DepositParams(TypedDict):
    token: TokenHelper
    amount: int


class Ticketer(ContractHelper):
    # TODO: consider moving this to some consts file?
    TICKET_TYPE_EXPRESSION = 'pair (nat %token_id) (option %token_info bytes)'

    default_storage = {
        'extra_metadata': {},
        'metadata': make_metadata(
            name='Ticketer',
            description='The Ticketer is a component of the Etherlink Bridge, designed to wrap legacy FA2 and FA1.2 tokens to tickets.',
        ),
        'token_ids': {},
        'tokens': {},
        'next_token_id': 0,
    }

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Ticketer with empty storage"""

        filename = join(get_build_dir(), 'ticketer.tz')
        return cls.originate_from_file(filename, client, cls.default_storage)

    @classmethod
    def originate_with_external_metadata(
            cls,
            client: PyTezosClient,
            # TODO: add type for key as fa2 or fa12 token
            external_metadata: dict[Any, dict[str, bytes]],
        ) -> OperationGroup:
        """Deploys Ticketer with external metadata"""

        storage = cls.default_storage.copy()
        storage['extra_metadata'] = external_metadata

        filename = join(get_build_dir(), 'ticketer.tz')
        return cls.originate_from_file(filename, client, storage)

    def deposit(self, params: DepositParams) -> ContractCall:
        """ Deposits given amount of given token to the contract """

        return self.contract.deposit({
            'token': params['token'].as_dict(),
            'amount': params['amount'],
        })

    def get_token_id(self, token: TokenHelper) -> int:
        """ Returns internal ticketer token id for given token
            NOTE: if given token is not in storage, returned token id will
                be equal to next_token_id, which allow to create ticket
                params before token added to the storage (in bacth call)
        """

        token_ids = self.contract.storage['token_ids']
        try:
            token_id = token_ids[token.as_dict()]()  # type: ignore
        except KeyError:
            token_id = self.contract.storage['next_token_id']()

        assert type(token_id) is int
        return token_id
