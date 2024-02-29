from pytezos.client import PyTezosClient
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup

from scripts.helpers.contracts.tokens.token import TokenHelper
from scripts.helpers.utility import pack
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)

FA2AsDictType = dict[str, tuple[str, int]]
FA2AsTupleType = tuple[str, tuple[str, int]]


class FA2(TokenHelper):
    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        return cls.originate(client, {})

    def allow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        return self.contract.update_operators(
            [
                {
                    'add_operator': {
                        'owner': get_address(owner),
                        'operator': get_address(operator),
                        'token_id': self.token_id,
                    }
                }
            ]
        )

    def disallow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        return self.contract.update_operators(
            [
                {
                    'remove_operator': {
                        'owner': get_address(owner),
                        'operator': get_address(operator),
                        'token_id': self.token_id,
                    }
                }
            ]
        )

    def as_dict(self) -> FA2AsDictType:
        return {'fa2': (self.address, self.token_id)}

    def as_tuple(self) -> FA2AsTupleType:
        return ('fa2', (self.address, self.token_id))

    def get_balance(self, client_or_contract: Addressable) -> int:
        address = get_address(client_or_contract)
        key = (address, self.token_id)
        balance = self.contract.storage['ledger'][key]()  # type: ignore
        assert isinstance(balance, int)
        return balance

    def make_token_info(self) -> dict[str, bytes]:
        return {
            'contract_address': pack(self.address, 'address'),
            'token_type': pack("FA2", 'string'),
            'token_id': pack(self.token_id, 'nat'),
        }

    @classmethod
    def originate(
        cls, client: PyTezosClient, balances: dict[Addressable, int], token_id: int = 0
    ) -> OperationGroup:
        raise NotImplementedError("FA2 generic originate not implemented")
