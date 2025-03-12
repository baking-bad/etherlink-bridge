from os.path import join

from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup

from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.utility import get_build_dir
from scripts.helpers.utility import originate_from_file


class Exchanger(ContractHelper):
    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
    ) -> OperationGroup:
        """Deploys Exchanger (native xtz ticketer) contract"""

        filename = join(get_build_dir(), "exchanger.tz")
        storage: dict = {}
        return originate_from_file(filename, client, storage)
