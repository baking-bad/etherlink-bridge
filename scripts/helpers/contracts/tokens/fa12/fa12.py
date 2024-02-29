from scripts.helpers.contracts.tokens.token import TokenHelper
from scripts.helpers.utility import pack
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
            'contract_address': pack(self.address, 'address'),
            'token_type': pack("FA1.2", 'string'),
        }
