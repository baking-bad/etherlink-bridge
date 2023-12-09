from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import (
    DEFAULT_ADDRESS,
    pack,
    get_build_dir,
)
from typing import (
    TypedDict,
    Optional,
    Union,
)
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup
from os.path import join
from tests.helpers.metadata import make_metadata


class DepositParams(TypedDict):
    data: bytes
    receiver: str


class ReleaseParams(TypedDict):
    data: str
    receiver: str


class BaseProxy(ContractHelper):
    default_storage = {
        'context': {},
        'metadata': make_metadata(),
    }
    filename = 'filename-not-set'

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Proxy with empty storage"""

        return cls.originate_from_file(cls.filename, client, cls.default_storage)

    def get_context(self, address: str) -> Optional[dict]:
        try:
            return dict(self.contract.storage['context'][address]())
        except KeyError:
            return None


class DepositProxy(BaseProxy):
    default_storage = {
        'context': {},
        'metadata': make_metadata(
            name='Deposit Proxy',
            description='THe Deposit Proxy is a component of the Etherlink Bridge, used to enable the transfer of implicit address tickets to the Etherlink Rollup contract to the deposit entrypoint on L1 side.',
        ),
    }
    filename = join(get_build_dir(), 'proxies', 'deposit.tz')

    def set(self, params: DepositParams) -> ContractCall:
        return self.contract.set(params)


class ReleaseProxy(BaseProxy):
    default_storage = {
        'context': {},
        'metadata': make_metadata(
            name='Release Proxy',
            description='The Release Proxy is a component of the Bridge Protocol Prototype, used to enable the transfer of implicit address tickets to the Ticketer contract to the %release entrypoint on L1 side.',
        ),
    }
    filename = join(get_build_dir(), 'proxies', 'release.tz')

    def set(self, params: ReleaseParams) -> ContractCall:
        return self.contract.set(params)
