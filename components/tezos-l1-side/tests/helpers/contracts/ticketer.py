from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import (
    get_build_dir,
    to_michelson_type,
    to_micheline,
    pack,
    DEFAULT_ADDRESS,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from typing import (
    Any,
    TypedDict,
)
from os.path import join
from tests.helpers.metadata import make_metadata
from tests.helpers.contracts.tokens import (
    TicketContent,
    TokenHelper,
    TokenInfo,
    TokenAsDictType,
)
from tests.helpers.tickets import Ticket


class DepositParams(TypedDict):
    amount: int


class Ticketer(ContractHelper):
    # Ticket content type is fixed to match FA2.1 ticket content type:
    TICKET_CONTENT_TYPE = '(pair nat (option bytes))'

    @staticmethod
    def make_storage(
            token_as_dict: TokenAsDictType,
            content: TicketContent,
        ) -> dict[str, Any]:
        metadata = make_metadata(
            name='Ticketer',
            description='The Ticketer is a component of the Etherlink Bridge, designed to wrap legacy FA2 and FA1.2 tokens to tickets.',
        )
        return {
            'content': content,
            'token': token_as_dict,
            'metadata': metadata,
        }

    @classmethod
    def originate(
            cls,
            client: PyTezosClient,
            token: TokenHelper,
            extra_token_info: TokenInfo,
            token_id: int = 0,
        ) -> OperationGroup:
        """Deploys Ticketer with given Token and extra token info"""

        storage = cls.make_storage(
            token.as_dict(),
            token.make_content(extra_token_info, token_id),
        )
        filename = join(get_build_dir(), 'ticketer.tz')
        return cls.originate_from_file(filename, client, storage)

    def deposit(self, params: DepositParams) -> ContractCall:
        """ Deposits given amount of given token to the contract """

        return self.contract.deposit(params['amount'])

    def get_ticket(self, amount: int = 0) -> Ticket:
        """Returns ticket with given content and amount that can be used in
            `ticket_transfer` call"""

        content = to_michelson_type(
            self.contract.storage['content'](),
            self.TICKET_CONTENT_TYPE,
        ).to_micheline_value()

        return {
            'ticketer': self.address,
            'content_type': to_micheline(self.TICKET_CONTENT_TYPE),
            'content': content,
            'amount': amount,
        }
