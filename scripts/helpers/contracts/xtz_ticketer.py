from os.path import join
from typing import Optional

from pytezos.client import PyTezosClient
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup

from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.ticket_content import TicketContent
from scripts.helpers.ticket import Ticket
from scripts.helpers.utility import get_build_dir
from scripts.helpers.utility import originate_from_file


class XtzTicketer(ContractHelper):
    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
    ) -> OperationGroup:
        """Deploys XtzTicketer (exchanger) contract"""

        filename = join(get_build_dir(), "xtz-ticketer.tz")
        storage: dict = {}
        return originate_from_file(filename, client, storage)

    def read_ticket(
        self,
        owner: Optional[Addressable] = None,
    ) -> Ticket:
        """Returns ticket with XtzTicketer's content that can be used in
        `ticket_transfer` call. Amount is set to the client's balance."""

        owner = owner or self.client
        return Ticket.create(
            client=self.client,
            owner=owner,
            ticketer=self.address,
            content=TicketContent(0, None),
        )

    def mint(
        self,
        target: Addressable,
        mutez_amount: int,
    ) -> ContractCall:
        """Mints ticket for the given owner"""

        return self.contract.mint(get_address(target)).with_amount(mutez_amount)
