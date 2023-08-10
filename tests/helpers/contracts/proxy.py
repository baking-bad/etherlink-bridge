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


class RouterSetParams(TypedDict):
    data: RoutingData
    receiver: str


class TicketerSetParams(TypedDict):
    data: str
    receiver: str


class RoutingDataAndRouter(TypedDict):
    routing_data: RoutingData
    router: str


class L2BurnSetParams(TypedDict):
    data: RoutingDataAndRouter
    receiver: str


class BaseProxy(ContractHelper):
    default_storage = {}
    filename = 'filename-not-set'

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Proxy with empty storage"""

        return cls.originate_from_file(cls.filename, client, cls.default_storage)


class ProxyRouter(BaseProxy):
    filename = make_filename_from_build_name('proxy-router')

    def set(self, params: RouterSetParams) -> ContractCall:
        return self.contract.set(params)


class ProxyTicketer(BaseProxy):
    filename = make_filename_from_build_name('proxy-ticketer')

    def set(self, params: TicketerSetParams) -> ContractCall:
        return self.contract.set(params)


class ProxyL2Burn(BaseProxy):
    filename = make_filename_from_build_name('proxy-l2-burn')

    def set(self, params: L2BurnSetParams) -> ContractCall:
        return self.contract.set(params)
