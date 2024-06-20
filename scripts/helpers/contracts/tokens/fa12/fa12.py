from scripts.helpers.contracts.tokens.token import TokenHelper
from pytezos.client import PyTezosClient
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)


FA12AsDictType = dict[str, str]
FA12AsTupleType = tuple[str, str]


class FA12(TokenHelper):
    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        return cls.originate(client, {})

    def allow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        # Allow makes approval for the total supply of the token
        return self.contract.approve(
            {
                'spender': get_address(operator),
                'value': self.contract.storage['total_supply'](),
            }
        )

    def disallow(self, owner: Addressable, operator: Addressable) -> ContractCall:
        # Revoke allowance
        return self.contract.approve(
            {
                'spender': get_address(operator),
                'value': 0,
            }
        )

    def as_dict(self) -> FA12AsDictType:
        return {'fa12': self.address}

    def as_tuple(self) -> FA12AsTupleType:
        return ('fa12', self.address)

    def make_token_info(self) -> dict[str, bytes]:
        return {
            'contract_address': self.address.encode('utf-8'),
            'token_type': "FA1.2".encode('utf-8'),
        }

    def get_balance(self, client_or_contract: Addressable) -> int:
        raise NotImplementedError("FA1.2 generic get_balance not implemented")

    @classmethod
    def originate(
        cls, client: PyTezosClient, balances: dict[Addressable, int], token_id: int = 0
    ) -> OperationGroup:
        raise NotImplementedError("FA1.2 generic originate not implemented")
