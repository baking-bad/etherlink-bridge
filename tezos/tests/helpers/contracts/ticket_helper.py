from tezos.tests.helpers.utility import DEFAULT_ADDRESS
from tezos.tests.helpers.contracts import (
    ContractHelper,
    TokenHelper,
    Ticketer,
)
from pytezos.client import PyTezosClient
from tezos.tests.helpers.utility import get_build_dir
from pytezos.operation.group import OperationGroup
from os.path import join
from tezos.tests.helpers.metadata import Metadata
from pytezos.contract.call import ContractCall


class TicketHelper(ContractHelper):
    default_storage = {
        'token': {'fa2': (DEFAULT_ADDRESS, 0)},
        'ticketer': DEFAULT_ADDRESS,
        'context': None,
        'metadata': Metadata.make_default(
            name='Ticket Helper',
            description='The Ticket Helper is a helper contract which helps user to communicate with Etherlink Bridge components that requires tickets to be packed into external data structure.',
        ),
    }

    filename = join(get_build_dir(), 'ticket-helper.tz')

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Ticket Helper"""

        return cls.originate_from_file(cls.filename, client, cls.default_storage)

    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
        token: TokenHelper,
        ticketer: Ticketer,
    ) -> OperationGroup:
        """Deploys Ticket Helper"""

        storage = cls.default_storage.copy()
        storage['token'] = token.as_dict()
        storage['ticketer'] = ticketer.address

        return cls.originate_from_file(cls.filename, client, storage)

    def deposit(self, rollup: str, routing_info: bytes, amount: int) -> ContractCall:
        """Deposits given amount of tokens to the L2 address set in routing data"""

        return self.contract.deposit(
            {'rollup': rollup, 'routing_info': routing_info, 'amount': amount}
        )
