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


class BaseProxy(ContractHelper):
    default_storage = {}
    filename = 'filename-not-set'

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Proxy with empty storage"""

        return cls.originate_from_file(cls.filename, client, cls.default_storage)

    def set(self, params: SetParams) -> ContractCall:
        return self.contract.set(params)

class ProxyRouter(BaseProxy):
    filename = make_filename_from_build_name('proxy-router')

class ProxyTicketer(BaseProxy):
    filename = make_filename_from_build_name('proxy-ticketer')
