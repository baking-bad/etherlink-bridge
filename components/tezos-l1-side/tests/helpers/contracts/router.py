from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import get_build_dir
from pytezos.operation.group import OperationGroup
from os.path import join
from tests.helpers.metadata import make_metadata


class Router(ContractHelper):
    default_storage = {
        'unit': None,
        'metadata': make_metadata(
            name='Router for Withdrawals',
            description='The Router for Withdrawals is a component of the Etherlink Bridge which processing L2 -> L1 withdrawals.',
        )
    }

    filename = join(get_build_dir(), 'router.tz')

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Router"""

        return cls.originate_from_file(cls.filename, client, cls.default_storage)
