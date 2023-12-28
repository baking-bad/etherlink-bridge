from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeTestCase
from tezos.tests.helpers.contracts import (
    Ticketer,
    RollupMock,
    FA2,
    FA12,
    TokenHelper,
    ContractHelper,
    Router,
    TicketHelper,
)
from tezos.tests.helpers.utility import pkh, pack
from typing import Type, TypeVar, TypedDict, Optional


class BaseTestCase(SandboxedNodeTestCase):
    accounts: list = []

    def bootstrap_account(self, n: Optional[int] = None) -> PyTezosClient:
        """Creates bootstrap account with given number"""

        accs_count = n or len(self.accounts)
        # TODO: consider adding some Account abstraction with `address` property
        bootstrap: PyTezosClient = self.client.using(key=f'bootstrap{accs_count + 1}')
        bootstrap.reveal()
        self.accounts.append(bootstrap)
        return bootstrap

    def deploy_fa2(self, balances: dict[str, int]) -> FA2:
        """Deploys FA2 contract with given balances"""

        opg = FA2.originate(self.manager, balances).send()
        self.bake_block()
        return FA2.create_from_opg(self.manager, opg)

    def deploy_fa12(self, balances: dict[str, int]) -> FA12:
        """Deploys FA12 contract with given balances"""

        opg = FA12.originate(self.manager, balances).send()
        self.bake_block()
        return FA12.create_from_opg(self.manager, opg)

    def deploy_rollup_mock(self) -> RollupMock:
        """Deploys RollupMock contract"""

        opg = RollupMock.originate_default(self.manager).send()
        self.bake_block()
        return RollupMock.create_from_opg(self.manager, opg)

    def deploy_router(self) -> Router:
        """Deploys Router contract"""

        opg = Router.originate_default(self.manager).send()
        self.bake_block()
        return Router.create_from_opg(self.manager, opg)

    def deploy_ticketer(
        self,
        token: TokenHelper,
        extra_metadata: Optional[dict[str, bytes]] = None,
    ) -> Ticketer:
        """Deploys Ticketer contract with given token and additional metadata"""

        extra_metadata = extra_metadata or {}
        opg = Ticketer.originate(self.manager, token, extra_metadata).send()
        self.bake_block()
        return Ticketer.create_from_opg(self.manager, opg)

    def deploy_ticket_helper(
        self,
        token: TokenHelper,
        ticketer: Ticketer,
    ) -> TicketHelper:
        """Deploys TicketHelper contract with given token and ticketer"""

        opg = TicketHelper.originate(self.manager, ticketer).send()
        self.bake_block()
        return TicketHelper.create_from_opg(self.manager, opg)

    def setUp(self) -> None:
        self.accounts = []
        self.manager = self.bootstrap_account()
