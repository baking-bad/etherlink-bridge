from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeTestCase
from tests.helpers.contracts import (
    Ticketer,
    RollupMock,
    FA2,
    FA12,
    TokenHelper,
    ContractHelper,
    Router,
    TicketHelper,
)
from tests.helpers.utility import pkh, pack
from typing import Type, TypeVar, TypedDict


class TokenSet(TypedDict):
    token: TokenHelper
    ticketer: Ticketer
    helper: TicketHelper


class Contracts(TypedDict):
    rollup_mock: RollupMock
    fa2: TokenSet
    fa12: TokenSet
    router: Router


class BaseTestCase(SandboxedNodeTestCase):
    def activate_accs(self) -> None:
        # TODO: consider adding some Account abstraction with `address` property
        alice = self.client.using(key='bootstrap1')
        alice.reveal()

        boris = self.client.using(key='bootstrap2')
        boris.reveal()

        manager = self.client.using(key='bootstrap4')
        manager.reveal()
        self.accs = {
            'alice': alice,
            'boris': boris,
            'manager': manager,
        }

    def setUp(self) -> None:
        self.activate_accs()
        manager = self.accs['manager']

        # Contracts deployment:
        rollup_mock_opg = RollupMock.originate_default(manager).send()
        self.bake_block()
        rollup_mock = RollupMock.create_from_opg(manager, rollup_mock_opg)

        router_opg = Router.originate_default(manager).send()
        self.bake_block()
        router = Router.create_from_opg(manager, router_opg)

        # Tokens deployment:
        token_balances = {pkh(account): 1000 for account in self.accs.values()}

        fa2_opg = FA2.originate(manager, token_balances).send()
        self.bake_block()
        token_fa2 = FA2.create_from_opg(manager, fa2_opg)

        # Deploying Ticketer for FA2 with external metadata:
        fa2_external_metadata = {
            'decimals': pack(12, 'nat'),
            'symbol': pack('FA2', 'string'),
        }

        opg = Ticketer.originate(manager, token_fa2, fa2_external_metadata).send()
        self.bake_block()
        ticketer_fa2 = Ticketer.create_from_opg(manager, opg)

        # Deploying TicketHelper for FA2:
        opg = TicketHelper.originate(
            client=manager,
            token=token_fa2,
            ticketer=ticketer_fa2,
        ).send()
        self.bake_block()
        helper_fa2 = TicketHelper.create_from_opg(manager, opg)

        # Deploying Ticketer for FA1.2 with external metadata:
        fa12_external_metadata = {
            'decimals': pack(0, 'nat'),
            'symbol': pack('FA1.2', 'string'),
        }

        fa12_opg = FA12.originate(manager, token_balances).send()
        self.bake_block()
        token_fa12 = FA12.create_from_opg(manager, fa12_opg)

        opg = Ticketer.originate(manager, token_fa12, fa12_external_metadata).send()
        self.bake_block()
        ticketer_fa12 = Ticketer.create_from_opg(manager, opg)

        # Deploying TicketHelper for FA12:
        opg = TicketHelper.originate(
            client=manager,
            token=token_fa12,
            ticketer=ticketer_fa12,
        ).send()
        self.bake_block()
        helper_fa12 = TicketHelper.create_from_opg(manager, opg)

        self.contracts: Contracts = {
            'rollup_mock': rollup_mock,
            'fa2': {
                'token': token_fa2,
                'ticketer': ticketer_fa2,
                'helper': helper_fa2,
            },
            'fa12': {
                'token': token_fa12,
                'ticketer': ticketer_fa12,
                'helper': helper_fa12,
            },
            'router': router,
        }
