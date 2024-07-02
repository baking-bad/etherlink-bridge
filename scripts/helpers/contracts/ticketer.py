from os.path import join
from typing import Any

from eth_abi import decode  # type: ignore
from pytezos.client import PyTezosClient
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup
from web3 import Web3

from scripts.helpers.addressable import Addressable
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.contracts.tokens import TokenHelper
from scripts.helpers.contracts.tokens import TokenInfo
from scripts.helpers.metadata import Metadata
from scripts.helpers.ticket import Ticket
from scripts.helpers.ticket_content import TicketContent
from scripts.helpers.utility import get_build_dir
from scripts.helpers.utility import originate_from_file


class Ticketer(ContractHelper):
    @staticmethod
    def make_storage(
        token: TokenHelper,
        extra_token_info: TokenInfo,
        content_token_id: int = 0,
    ) -> dict[str, Any]:
        """Creates storage for the Ticketer contract"""

        symbol = extra_token_info.get('symbol') if extra_token_info else None
        metadata = Metadata.make_default(
            name=f'Ticketer: {symbol}' if symbol else 'Ticketer',
            description='The Ticketer is a component of the Etherlink Bridge, designed to wrap legacy FA2 and FA1.2 tokens to tickets.',
        )
        content = (content_token_id, token.make_token_info_bytes(extra_token_info))
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

    def read_content(self) -> TicketContent:
        """Returns content of the ticketer"""

        raw_content = self.contract.storage['content']()
        return TicketContent(
            token_id=raw_content[0],
            token_info=raw_content[1],
        )

    def read_ticket(
        self,
        owner: Addressable,
    ) -> Ticket:
        """Returns ticket with Ticketer's content that can be used in
        `ticket_transfer` call. Amount is set to the client's balance."""

        return Ticket.create(
            client=self.client,
            owner=owner,
            ticketer=self.address,
            content=self.read_content(),
        )

    def get_token(self) -> TokenHelper:
        """Returns token helper"""

        token = self.contract.storage['token']()
        assert isinstance(token, dict)
        return TokenHelper.from_dict(self.client, token)

    def get_total_supply_view(self) -> int:
        """Returns total supply of tickets"""

        return self.contract.get_total_supply().run_view()  # type: ignore

    def get_content_view(self) -> tuple[int, bytes]:
        """Returns content of the ticketer"""

        return self.contract.get_content().run_view()  # type: ignore

    def get_token_view(self) -> dict[str, Any]:
        """Returns token info"""

        return self.contract.get_token().run_view()  # type: ignore

    @staticmethod
    def get_ticket_hash(ticketer_params: dict[str, str]) -> int:
        data = Web3.solidity_keccak(
            ['bytes22', 'bytes'],
            [
                '0x' + ticketer_params['address_bytes'],
                '0x' + ticketer_params['content_bytes'],
            ],
        )
        ticket_hash: int = decode(['uint256'], data)[0]
        return ticket_hash

    def get_content_bytes_hex(self) -> str:
        """Returns content of the ticketer as bytes hex string"""

        return self.read_ticket(self.address).content.to_bytes_hex()
