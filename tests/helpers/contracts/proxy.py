from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import (
    DEFAULT_ADDRESS,
    make_filename_from_build_name,
    pack,
)
from tests.helpers.routing_data import RoutingData
from typing import TypedDict
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup


class SetParams(TypedDict):
    data: RoutingData
    receiver: str


class Proxy(ContractHelper):
    default_storage = {}

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Proxy with empty storage"""

        filename = make_filename_from_build_name('proxy-rollup-deposit')
        return cls.originate_from_file(filename, client, cls.default_storage)

    def set(self, params: SetParams) -> ContractCall:
        return self.contract.set(params)
