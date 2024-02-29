from tezos.tests.helpers.utility import (
    originate_from_file,
    get_build_dir,
)
from tezos.tests.helpers.contracts import (
    ContractHelper,
    TokenHelper,
    Ticketer,
)
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from os.path import join
from tezos.tests.helpers.metadata import Metadata
from pytezos.contract.call import ContractCall
from tezos.tests.helpers.addressable import (
    Addressable,
    get_address,
)
from typing import Optional


class TicketHelper(ContractHelper):
    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
        ticketer: Ticketer,
        erc_proxy: bytes,
        token: Optional[TokenHelper] = None,
    ) -> OperationGroup:
        """Deploys Ticket Helper"""

        token = token or ticketer.get_token()
        storage = {
            'token': token.as_dict(),
            'ticketer': ticketer.address,
            'erc_proxy': erc_proxy,
            'context': None,
            'metadata': Metadata.make_default(
                name='Ticket Helper',
                description='The Ticket Helper is a helper contract which helps user to communicate with Etherlink Bridge components that requires tickets to be packed into external data structure.',
            ),
        }
        filename = join(get_build_dir(), 'ticket-helper.tz')

        return originate_from_file(filename, client, storage)

    def deposit(self, rollup: Addressable, receiver: bytes, amount: int) -> ContractCall:
        """Deposits given amount of tokens to the L2 address set in routing data"""

        deposit_params = {
            'rollup': get_address(rollup),
            'receiver': receiver,
            'amount': amount
        }
        return self.contract.deposit(deposit_params)

    def get_ticketer(self) -> Ticketer:
        """Returns ticketer"""

        ticketer_address = self.contract.storage['ticketer']()
        assert isinstance(ticketer_address, str)
        return Ticketer.from_address(self.client, ticketer_address)
