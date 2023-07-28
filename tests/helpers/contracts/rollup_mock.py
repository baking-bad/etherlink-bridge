from tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tests.helpers.utility import make_filename_from_build_name
from pytezos.operation.group import OperationGroup
from pytezos.rpc.query import RpcQuery


class RollupMock(ContractHelper):
    default_storage = {
        'tickets': {},
        'messages': {},
        'next_id': 0,
    }

    @classmethod
    def originate_default(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys Locker with empty storage"""

        filename = make_filename_from_build_name('rollup-mock')
        return cls.originate_from_file(filename, client, cls.default_storage)

    # TODO: consider improving this generic list type
    def get_tickets(self) -> list:
        """Returns list of tickets in storage"""

        # TODO: this is probably not the best / easiest way to make RPC call,
        # need to research more to find good way to do this:
        query = RpcQuery(
            node=self.client.shell.node,
            path='/chains/{}/blocks/{}/context/contracts/{}/all_ticket_balances',
            params=[
                'main',
                self.client.shell.blocks()[0][0],
                self.address
            ]
        )

        # TODO: also this is probably good idea to have some Account abstraction
        # with possibility to get address, balance and all tickets both for
        # implicit and originated accounts

        result = query()
        assert type(result) is list
        return result
