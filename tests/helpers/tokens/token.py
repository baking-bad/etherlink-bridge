from abc import ABC, abstractmethod
from tests.helpers.contract import ContractHelper
from typing import Union, Tuple
from pytezos.contract.call import ContractCall
from tests.utility import pack


FA2AsDictType = dict[str, Union[str, Tuple[str, int]]]


class TokenHelper(ContractHelper):
    # TODO: consider moving this to some consts file?
    MAP_TOKEN_INFO_TYPE = 'map %token_info string bytes'


    @abstractmethod
    def allow(self, operator: str) -> ContractCall:
        pass

    @abstractmethod
    def as_dict(self) -> FA2AsDictType:
        pass

    @abstractmethod
    def get_balance(self, address: str) -> int:
        pass

    @abstractmethod
    def make_token_info(self) -> dict[str, bytes]:
        pass

    def make_token_info_bytes(self) -> bytes:
        return pack(self.make_token_info(), self.MAP_TOKEN_INFO_TYPE)
