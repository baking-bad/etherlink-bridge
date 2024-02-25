from tezos.tests.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from tezos.tests.helpers.utility import (
    get_build_dir,
    originate_from_file,
    DEFAULT_ADDRESS,
)
from pytezos.operation.group import OperationGroup
from os.path import join
from tezos.tests.helpers.metadata import Metadata
from typing import (
    Optional,
    Any,
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

    def mint(self, micheline_content: dict, amount: int) -> OperationGroup:
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

    def set(
        self,
        target: str,
        entrypoint: dict[str, Any],
        xtz_amount: int = 0,
    ) -> OperationGroup:
        """Sets the internal call parameters that will be used to wrap
        ticket at the next `mint` calls and redirect tickets for the
        next `default` or `withdraw` calls.

        Entrypoint is one of the following:
            - `default` can be used to send tickets to the implicit address
            - `routerWithdraw` can be used to test Router.withdraw entrypoint
                and unwrap tickets utilizing Ticketer.withdraw entrypoint
            - `rollupDeposit` to be used as TicketHelper without restrictions
                to test rollup operations
        """

        return self.contract.set(
            target=target,
            entrypoint=entrypoint,
            xtz_amount=xtz_amount,
        ).with_amount(xtz_amount)
