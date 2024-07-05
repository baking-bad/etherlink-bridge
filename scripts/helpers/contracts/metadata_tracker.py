from pytezos.client import PyTezosClient
from scripts.helpers.contracts.contract import ContractHelper
from pytezos.contract.call import ContractCall
from scripts.helpers.utility import originate_from_file
from scripts.helpers.utility import get_build_dir
from pytezos.operation.group import OperationGroup
from os.path import join


class MetadataTracker(ContractHelper):
    @classmethod
    def originate(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys MetadataTracker with empty storage"""

        filename = join(get_build_dir(), 'metadata-tracker.tz')
        return originate_from_file(filename, client, None)

    def default(self, metadata: bytes) -> ContractCall:
        """Makes transaction with metadata to the contract"""

        return self.contract.default(metadata)
