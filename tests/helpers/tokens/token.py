from abc import ABC, abstractmethod
from tests.helpers.contract import ContractHelper
from typing import Union, Tuple
from pytezos.contract.call import ContractCall


FA2AsDictType = dict[str, Union[str, Tuple[str, int]]]


class TokenHelper(ContractHelper):
    @abstractmethod
    def allow(self, operator: str) -> ContractCall:
        pass

    @abstractmethod
    def as_dict(self) -> FA2AsDictType:
        pass