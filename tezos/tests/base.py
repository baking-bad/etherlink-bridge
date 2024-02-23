from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.contract.result import ContractCallResult
from tezos.tests.helpers.contracts import (
    Ticketer,
    RollupMock,
    FA2,
    FA12,
    TokenHelper,
    Router,
    TicketHelper,
)
from typing import Optional


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
        return FA2.from_opg(self.manager, opg)

    def deploy_fa12(self, balances: dict[str, int]) -> FA12:
        """Deploys FA12 contract with given balances"""

        opg = FA12.originate(self.manager, balances).send()
        self.bake_block()
        return FA12.from_opg(self.manager, opg)

    def deploy_rollup_mock(self) -> RollupMock:
        """Deploys RollupMock contract"""

        opg = RollupMock.originate(self.manager).send()
        self.bake_block()
        return RollupMock.from_opg(self.manager, opg)

    def deploy_router(self) -> Router:
        """Deploys Router contract"""

        opg = Router.originate(self.manager).send()
        self.bake_block()
        return Router.from_opg(self.manager, opg)

    def deploy_ticketer(
        self,
        token: TokenHelper,
        extra_metadata: Optional[dict[str, bytes]] = None,
    ) -> Ticketer:
        """Deploys Ticketer contract with given token and additional metadata"""

        extra_metadata = extra_metadata or {}
        opg = Ticketer.originate(self.manager, token, extra_metadata).send()
        self.bake_block()
        return Ticketer.from_opg(self.manager, opg)

    def deploy_ticket_helper(
        self,
        token: TokenHelper,
        ticketer: Ticketer,
        erc_proxy: bytes,
    ) -> TicketHelper:
        """Deploys TicketHelper contract with given token and ticketer"""

        opg = TicketHelper.originate(self.manager, ticketer, erc_proxy).send()
        self.bake_block()
        return TicketHelper.from_opg(self.manager, opg)

    def setUp(self) -> None:
        self.accounts = []
        self.manager = self.bootstrap_account()

    def setup_fa2(
        self,
        balances: dict[str, int],
        extra_metadata: Optional[dict[str, bytes]] = None,
    ) -> tuple[FA2, Ticketer, bytes, TicketHelper]:
        """Returns FA2 setup with token, ticketer, erc_proxy and helper"""

        token = self.deploy_fa2(balances)
        ticketer = self.deploy_ticketer(token, extra_metadata)
        erc_proxy = bytes.fromhex('fa02fa02fa02fa02fa02fa02fa02fa02fa02fa02')
        helper = self.deploy_ticket_helper(token, ticketer, erc_proxy)
        return (token, ticketer, erc_proxy, helper)

    def setup_fa12(
        self,
        balances: dict[str, int],
        extra_metadata: Optional[dict[str, bytes]] = None,
    ) -> tuple[FA12, Ticketer, bytes, TicketHelper]:
        """Returns FA1.2 setup with token, ticketer, erc_proxy and helper"""

        token = self.deploy_fa12(balances)
        ticketer = self.deploy_ticketer(token, extra_metadata)
        erc_proxy = bytes.fromhex('fa12fa12fa12fa12fa12fa12fa12fa12fa12fa12')
        helper = self.deploy_ticket_helper(token, ticketer, erc_proxy)
        return (token, ticketer, erc_proxy, helper)

    def find_call_result(self, opg: OperationGroup) -> ContractCallResult:
        """Returns result of the last call in the given operation group"""

        blocks = self.manager.shell.blocks['head':]  # type: ignore
        operation = blocks.find_operation(opg.hash())
        return ContractCallResult.from_operation_group(operation)[0]
