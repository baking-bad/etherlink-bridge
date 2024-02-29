from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from pytezos.sandbox.node import SandboxedNodeTestCase
from pytezos.contract.result import ContractCallResult
from pytezos.operation.result import OperationResult
from tezos.tests.helpers.contracts import (
    Ticketer,
    RollupMock,
    FA2,
    FA12,
    TokenHelper,
    TicketRouterTester,
    TicketHelper,
)
from typing import Optional
from tezos.tests.helpers.addressable import Addressable


class BaseTestCase(SandboxedNodeTestCase):
    accounts: list = []

    def bootstrap_account(self, n: Optional[int] = None) -> PyTezosClient:
        """Creates bootstrap account with given number"""

        accs_count = n or len(self.accounts)
        bootstrap: PyTezosClient = self.client.using(key=f'bootstrap{accs_count + 1}')
        bootstrap.reveal()
        self.accounts.append(bootstrap)
        return bootstrap

    def deploy_fa2(self, balances: dict[Addressable, int], token_id: int = 0) -> FA2:
        """Deploys FA2 contract with given balances"""

        opg = FA2.originate(self.manager, balances, token_id).send()
        self.bake_block()
        return FA2.from_opg(self.manager, opg, token_id=token_id)

    def deploy_fa12(self, balances: dict[Addressable, int]) -> FA12:
        """Deploys FA12 contract with given balances"""

        opg = FA12.originate(self.manager, balances).send()
        self.bake_block()
        return FA12.from_opg(self.manager, opg)

    def deploy_rollup_mock(self) -> RollupMock:
        """Deploys RollupMock contract"""

        opg = RollupMock.originate(self.manager).send()
        self.bake_block()
        return RollupMock.from_opg(self.manager, opg)

    def deploy_ticket_router_tester(self) -> TicketRouterTester:
        """Deploys TicketRouterTester contract"""

        opg = TicketRouterTester.originate(self.manager).send()
        self.bake_block()
        return TicketRouterTester.from_opg(self.manager, opg)

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
        erc_proxy: bytes = bytes.fromhex('00' * 20),
    ) -> TicketHelper:
        """Deploys TicketHelper contract with given token and ticketer"""

        opg = TicketHelper.originate(
            self.manager, ticketer, erc_proxy, token=token
        ).send()
        self.bake_block()
        return TicketHelper.from_opg(self.manager, opg)

    def setUp(self) -> None:
        self.accounts = []
        self.manager = self.bootstrap_account()

    def default_setup(
        self,
        token_type: str = 'FA2',
        balance: int = 1000,
        extra_metadata: Optional[dict[str, bytes]] = None,
        token_id: int = 0,
    ) -> tuple[PyTezosClient, TokenHelper, Ticketer, TicketRouterTester]:

        alice = self.bootstrap_account()

        if token_type == 'FA2':
            token: TokenHelper = self.deploy_fa2(
                balances={alice: balance},
                token_id=token_id,
            )
        elif token_type == 'FA1.2':
            token = self.deploy_fa12(balances={alice: balance})
        else:
            raise ValueError(f'Unknown token type: {token_type}')

        ticketer = self.deploy_ticketer(token, extra_metadata)
        tester = self.deploy_ticket_router_tester()
        token.using(alice).allow(alice, ticketer).send()
        self.bake_block()
        return alice, token, ticketer, tester

    def find_call_result(self, opg: OperationGroup, idx: int = 0) -> OperationResult:
        """Returns result of the last call in the given operation group"""

        blocks = self.manager.shell.blocks['head':]  # type: ignore
        operation = blocks.find_operation(opg.hash())
        return ContractCallResult.from_operation_group(operation)[idx]
