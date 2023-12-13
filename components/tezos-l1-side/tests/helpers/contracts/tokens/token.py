from abc import ABC, abstractmethod
from tests.helpers.contracts.contract import ContractHelper
from typing import Union, Tuple
from pytezos.contract.call import ContractCall
from tests.helpers.utility import pack
from typing import Optional


TicketContent = Tuple[int, Optional[bytes]]

# TODO: consider moving these types to fa2.py and fa12.py
FA2AsDictType = dict[str, Tuple[str, int]]
FA12AsDictType = dict[str, str]

FA2AsTupleType = Tuple[str, Tuple[str, int]]
FA12AsTupleType = Tuple[str, str]

TokenAsDictType = Union[FA2AsDictType, FA12AsDictType]
TokenAsTupleType = Union[FA2AsTupleType, FA12AsTupleType]

TokenInfo = Optional[dict[str, bytes]]


class TokenHelper(ContractHelper):
    # Map token info type is the same as token info metadata in FA2:
    MAP_TOKEN_INFO_TYPE = 'map %token_info string bytes'


    @abstractmethod
    def allow(self, operator: str) -> ContractCall:
        pass

    @abstractmethod
    def as_dict(self) -> TokenAsDictType:
        pass

    @abstractmethod
    def as_tuple(self) -> TokenAsTupleType:
        pass

    @abstractmethod
    def get_balance(self, address: str) -> int:
        pass

    @abstractmethod
    def make_token_info(self) -> dict[str, bytes]:
        pass

    def make_token_info_bytes(self) -> bytes:
        return pack(self.make_token_info(), self.MAP_TOKEN_INFO_TYPE)

    def make_content(
            self,
            extra_token_info: TokenInfo,
            token_id: int = 0,
        ) -> TicketContent:

        extra_token_info = extra_token_info or {}
        token_info = {
            **self.make_token_info(),
            **extra_token_info,
        }

        return (token_id, pack(token_info, self.MAP_TOKEN_INFO_TYPE))
