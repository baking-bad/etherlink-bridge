from abc import abstractmethod
from tezos.tests.helpers.contracts.contract import ContractHelper
from pytezos.contract.call import ContractCall
from tezos.tests.helpers.utility import pack
from typing import Optional, Type
from pytezos.operation.group import OperationGroup
from pytezos.client import PyTezosClient
from dataclasses import dataclass
from tezos.tests.helpers.addressable import Addressable


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
        balances: dict[Addressable, int],
        token_id: int = 0,
    ) -> OperationGroup: ...

    @abstractmethod
    def allow(self, owner: Addressable, operator: Addressable) -> ContractCall: ...

    @abstractmethod
    def disallow(self, owner: Addressable, operator: Addressable) -> ContractCall: ...

    @abstractmethod
    def as_dict(self) -> dict: ...

    @abstractmethod
    def as_tuple(self) -> tuple: ...

    @abstractmethod
    def get_balance(self, client_or_contract: Addressable) -> int: ...

    @abstractmethod
    def make_token_info(self) -> dict[str, bytes]: ...

    def make_token_info_bytes(
        self,
        extra_token_info: Optional[TokenInfo] = None,
    ) -> bytes:
        extra_token_info = extra_token_info or {}
        token_info = {
            **self.make_token_info(),
            **extra_token_info,
        }

        return pack(token_info, MAP_TOKEN_INFO_TYPE)

    @classmethod
    def from_dict(cls, client: PyTezosClient, token_dict: dict) -> 'TokenHelper':
        """Creates TokenHelper from dict with token info"""

        from tezos.tests.helpers.contracts.tokens.fa12 import FA12
        from tezos.tests.helpers.contracts.tokens.fa2 import FA2

        if 'fa12' in token_dict:
            return FA12.from_address(client, token_dict['fa12'])

        if 'fa2' in token_dict:
            contract, token_id = token_dict['fa2']
            return FA2.from_address(client, contract, token_id=token_id)

        raise ValueError(f'Unknown token type: {token_dict}')

    @staticmethod
    def get_cls(token_type: str) -> Type['TokenHelper']:
        """Returns token class by token type string"""

        from tezos.tests.helpers.contracts.tokens.fa12 import FA12
        from tezos.tests.helpers.contracts.tokens.fa2 import FA2

        assert token_type in ['FA2', 'FA1.2']
        return FA12 if token_type == 'FA1.2' else FA2
