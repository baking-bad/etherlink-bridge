from tests.helpers.utility import DEFAULT_ADDRESS
from tests.helpers.contracts import (
    ContractHelper,
    Token,
)
from pytezos.client import PyTezosClient
from tests.helpers.utility import get_build_dir
from pytezos.operation.group import OperationGroup
from os.path import join
from tests.helpers.metadata import make_metadata
from pytezos.contract.call import ContractCall


class TicketHelper(ContractHelper):
    default_storage = {
        'rollup': DEFAULT_ADDRESS,
        'token': {
            'fa2': (DEFAULT_ADDRESS, 0)
        },
        'ticketer': DEFAULT_ADDRESS,
        'approve_amount': 0,
        'routing_data': None,
        'metadata': make_metadata(
            name='Ticket Helper',
            description='The Ticket Helper is a helper contract which helps user to communicate with Etherlink Bridge components that requires tickets to be packed into external data structure.',
        )
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
            rollup: str,
            token: Token,
            ticketer: str,
            approve_amount: int = 0,
        ) -> OperationGroup:
        """Deploys Ticket Helper"""

        storage = cls.default_storage.copy()
        storage['rollup'] = rollup
        storage['token'] = token.as_dict()
        storage['ticketer'] = ticketer
        storage['approve_amount'] = approve_amount

        return cls.originate_from_file(cls.filename, client, storage)

    def deposit(self, routing_data: bytes, amount: int) -> ContractCall:
        """Deposits given amount of tokens to the L2 address set in routing data"""

        return self.contract.deposit({
            'routing_data': routing_data,
            'amount': amount
        })
