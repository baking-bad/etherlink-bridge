from tezos.tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tezos.tests.helpers.utility import (
    get_build_dir,
    originate_from_file,
    DEFAULT_ADDRESS,
)
from pytezos.operation.group import OperationGroup
from pytezos.contract.call import ContractCall
from os.path import join
from tezos.tests.helpers.metadata import Metadata
from typing import Optional
from tezos.tests.helpers.addressable import (
    Addressable,
    get_address,
)


class TicketRouterTester(ContractHelper):
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

    def mint(self, micheline_content: dict, amount: int) -> ContractCall:
        """Mints given amount of tickets with given content"""

        def micheline_content_to_tuple(content) -> tuple[int, Optional[bytes]]:
            """Converts ticket content to the tuple form"""
            token_id = int(content['args'][0]['int'])
            token_info = None
            has_token_info = content['args'][1]['prim'] == 'Some'
            if has_token_info:
                token_info = bytes.fromhex(
                    content['args'][1]['args'][0]['bytes']
                )
            return (token_id, token_info)

        return self.contract.mint(
            content=micheline_content_to_tuple(micheline_content),
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
