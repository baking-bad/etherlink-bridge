from abc import ABC, abstractmethod
from tezos.tests.helpers.contracts.contract import ContractHelper
from pytezos.contract.call import ContractCall
from tezos.tests.helpers.utility import pack
from typing import Optional
from pytezos.operation.group import OperationGroup
from pytezos.client import PyTezosClient
from dataclasses import dataclass


TicketContent = tuple[int, Optional[bytes]]
TokenInfo = Optional[dict[str, bytes]]

# Map token info type is the same as token info metadata in FA2:
MAP_TOKEN_INFO_TYPE = 'map %token_info string bytes'


@dataclass
class TokenHelper(ContractHelper):
    token_id: int = 0

    @classmethod
    @abstractmethod
    def originate(
        cls,
        client: PyTezosClient,
        balances: dict[str, int],
        token_id: int = 0,
    ) -> OperationGroup:
        pass

    @abstractmethod
    def allow(self, owner: str, operator: str) -> ContractCall:
        pass

    @abstractmethod
    def as_dict(self) -> dict:
        pass

    @abstractmethod
    def as_tuple(self) -> tuple:
        pass

    @abstractmethod
    def get_balance(self, address: str) -> int:
        pass

    @abstractmethod
    def make_token_info(self) -> dict[str, bytes]:
        pass

    def make_token_info_bytes(self) -> bytes:
        return pack(self.make_token_info(), MAP_TOKEN_INFO_TYPE)

    def make_content(
        self,
        extra_token_info: Optional[TokenInfo] = None,
    ) -> TicketContent:
        extra_token_info = extra_token_info or {}
        token_info = {
            **self.make_token_info(),
            **extra_token_info,
        }

        return (self.token_id, pack(token_info, MAP_TOKEN_INFO_TYPE))

    @classmethod
    def from_dict(cls, client: PyTezosClient, token_dict: dict) -> 'TokenHelper':
        """Creates TokenHelper from dict with token info"""

        from tezos.tests.helpers.contracts.tokens.fa12 import FA12
        from tezos.tests.helpers.contracts.tokens.fa2 import FA2

        if 'fa12' in token_dict:
            return FA12.create_from_address(client, token_dict['fa12'])

        if 'fa2' in token_dict:
            contract, token_id = token_dict['fa2']
            return FA2.create_from_address(client, contract, token_id=token_id)

        raise ValueError(f'Unknown token type: {token_dict}')
