from tests.helpers.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.utility import DEFAULT_ADDRESS
from tests.utility import make_filename_from_build_name
from typing import TypedDict
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup


class SetParams(TypedDict):
    data: str
    receiver: str


class Proxy(ContractHelper):
    default_storage = {
        'data': DEFAULT_ADDRESS,
        'receiver': DEFAULT_ADDRESS,
    }

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Proxy with empty storage"""

        filename = make_filename_from_build_name('proxy')
        return cls.originate_from_file(filename, client, cls.default_storage)

    def set(self, params: SetParams) -> ContractCall:
        return self.contract.set(params)
