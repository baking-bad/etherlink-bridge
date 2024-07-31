from scripts.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from scripts.helpers.utility import (
    get_build_dir,
    originate_from_file,
    DEFAULT_ADDRESS,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from os.path import join
from scripts.helpers.metadata import Metadata
from scripts.helpers.addressable import (
    Addressable,
    get_address,
)
from scripts.helpers.ticket_content import TicketContent


class TicketRouterTester(ContractHelper):
    # TODO: consider change `originate` to `make_originate_opg` for all tezos contracts
    #       and also it would be good to have real `originate` with wait and
    #       returning an actual object
    @classmethod
    def originate(cls, client: PyTezosClient) -> OperationGroup:
        """Deploys TicketRouterTester"""

        storage = {
            'internal_call': {
                'target': DEFAULT_ADDRESS,
                'entrypoint': {'default': None},
                'xtz_amount': 0,
            },
            'metadata': Metadata.make_default(
                name='Ticket Router Tester',
                description='The Ticket Router Tester is a helper contract allowing mint, deposit and withdraw tickets testing for the Etherlink Bridge contracts.',
            ),
        }

        filename = join(get_build_dir(), 'ticket-router-tester.tz')

        return originate_from_file(filename, client, storage)

    def mint(self, content: TicketContent, amount: int) -> ContractCall:
        """Mints given amount of tickets with given content"""

        return self.contract.mint(
            content=content.to_tuple(),
            amount=amount,
        )

    def set_router_withdraw(
        self,
        target: Addressable,
        receiver: Addressable,
        xtz_amount: int = 0,
    ) -> ContractCall:
        """Sets the internal call parameters to `withdraw` entrypoint of
        the Router interface which have the following michelson signature:
            pair %withdraw
                (address %receiver)
                (ticket %ticket (pair nat (option bytes)))

        This is the entrypoint which should receive ticket from
        TicketRouterTester at the next `mint`, `default` or `withdraw` calls.
        """

        return self.contract.set(
            target=get_address(target),
            entrypoint={'routerWithdraw': get_address(receiver)},
            xtz_amount=xtz_amount,
        ).with_amount(xtz_amount)

    def set_rollup_deposit(
        self,
        target: Addressable,
        routing_info: bytes,
        xtz_amount: int = 0,
    ) -> ContractCall:
        """Sets the internal call parameters to `deposit` entrypoint of
        the Etherlink rollup interface which have the following michelson
        signature:
            or %rollup
                (or
                    (pair %deposit
                        (bytes %routing_info)
                        (ticket %ticket (pair nat (option bytes))))
                    (bytes %b))
                (bytes %c)

        This is the entrypoint which should receive ticket from
        TicketRouterTester at the next `mint`, `default` or `withdraw` calls.
        """

        return self.contract.set(
            target=get_address(target),
            entrypoint={'rollupDeposit': routing_info},
            xtz_amount=xtz_amount,
        ).with_amount(xtz_amount)

    def set_default(
        self,
        target: Addressable,
        xtz_amount: int = 0,
    ) -> ContractCall:
        """Sets the internal call parameters to `default` entrypoint which
        allows to send tickets to the implicit address.
        Michelson signature: `ticket %default (pair nat (option bytes))`

        This is the entrypoint which should receive ticket from
        TicketRouterTester at the next `mint`, `default` or `withdraw` calls.
        """

        return self.contract.set(
            target=get_address(target),
            entrypoint={'default': None},
            xtz_amount=xtz_amount,
        ).with_amount(xtz_amount)
