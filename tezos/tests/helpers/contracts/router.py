from tezos.tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tezos.tests.helpers.utility import (
    get_build_dir,
    originate_from_file,
)
from pytezos.operation.group import OperationGroup
from os.path import join
from tezos.tests.helpers.metadata import Metadata


class Router(ContractHelper):
    @classmethod
    def originate(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Router"""

        storage = {
            'unit': None,
            'metadata': Metadata.make_default(
                name='Router for Withdrawals',
                description='The Router for Withdrawals is a component of the Etherlink Bridge which processing L2 -> L1 withdrawals.',
            ),
        }

        filename = join(get_build_dir(), 'router.tz')

        return originate_from_file(filename, client, storage)
