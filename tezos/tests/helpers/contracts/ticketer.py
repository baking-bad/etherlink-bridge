from tezos.tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tezos.tests.helpers.utility import (
    get_build_dir,
    to_michelson_type,
    to_micheline,
    originate_from_file,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from typing import Any
from os.path import join
from tezos.tests.helpers.metadata import Metadata
from tezos.tests.helpers.contracts.tokens import (
    TokenHelper,
    TokenInfo,
)
from tezos.tests.helpers.tickets import Ticket


# Ticket content type is fixed to match FA2.1 ticket content type:
TICKET_CONTENT_TYPE = '(pair nat (option bytes))'


class Ticketer(ContractHelper):
    @staticmethod
    def make_storage(
        token: TokenHelper,
        extra_token_info: TokenInfo,
    ) -> dict[str, Any]:
        metadata = Metadata.make_default(
            name='Ticketer',
            description='The Ticketer is a component of the Etherlink Bridge, designed to wrap legacy FA2 and FA1.2 tokens to tickets.',
        )
        content = token.make_content(extra_token_info)
        return {
            'content': content,
            'token': token.as_dict(),
            'total_supply': 0,
            'metadata': metadata,
        }

    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
        token: TokenHelper,
        extra_token_info: TokenInfo,
    ) -> OperationGroup:
        """Deploys Ticketer with given Token and extra token info"""

        storage = cls.make_storage(token, extra_token_info)
        filename = join(get_build_dir(), 'ticketer.tz')
        return originate_from_file(filename, client, storage)

    def deposit(self, amount: int) -> ContractCall:
        """Deposits given amount of given token to the contract"""

        return self.contract.deposit(amount)

    def get_ticket(self, amount: int = 0) -> Ticket:
        """Returns ticket with given content and amount that can be used in
        `ticket_transfer` call"""

        content = to_michelson_type(
            self.contract.storage['content'](),
            TICKET_CONTENT_TYPE,
        ).to_micheline_value()

        return Ticket(
            client=self.client,
            ticketer=self.address,
            content_type=to_micheline(TICKET_CONTENT_TYPE),
            content=content,
            amount=amount,
        )

    def get_token(self) -> TokenHelper:
        """Returns token helper"""

        token = self.contract.storage['token']()
        assert isinstance(token, dict)
        return TokenHelper.from_dict(self.client, token)
