from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import (
    DEFAULT_ADDRESS,
    pack,
    get_build_dir,
)
from tests.helpers.routing_data import RoutingData
from typing import (
    TypedDict,
    Optional,
)
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup
from os.path import join


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

    def get_context(self, address: str) -> Optional[dict]:
        try:
            return dict(self.contract.storage[address]())
        except KeyError:
            return None


class ProxyRouter(BaseProxy):
    filename = join(get_build_dir(), 'proxies', 'router.tz')

    def set(self, params: RouterSetParams) -> ContractCall:
        return self.contract.set(params)


class ProxyTicketer(BaseProxy):
    filename = join(get_build_dir(), 'proxies', 'ticketer.tz')

    def set(self, params: TicketerSetParams) -> ContractCall:
        return self.contract.set(params)


class ProxyL2Burn(BaseProxy):
    filename = join(get_build_dir(), 'proxies', 'l2-burn.tz')

    def set(self, params: L2BurnSetParams) -> ContractCall:
        return self.contract.set(params)
