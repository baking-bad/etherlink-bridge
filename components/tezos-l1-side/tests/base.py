from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeTestCase
from tests.helpers.contracts import (
    Ticketer,
    DepositProxy,
    ReleaseProxy,
    RollupMock,
    FA2,
    ContractHelper,
    Router,
    TicketHelper,
)
from tests.helpers.utility import pkh, pack
from typing import Type, TypeVar, TypedDict


class Contracts(TypedDict):
    deposit_proxy: DepositProxy
    release_proxy: ReleaseProxy
    rollup_mock: RollupMock
    fa2: FA2
    ticketer: Ticketer
    router: Router
    ticket_helper: TicketHelper


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
        deposit_proxy_opg = DepositProxy.originate_default(manager).send()
        self.bake_block()
        deposit_proxy = DepositProxy.create_from_opg(manager, deposit_proxy_opg)

        release_proxy_opg = ReleaseProxy.originate_default(manager).send()
        self.bake_block()
        release_proxy = ReleaseProxy.create_from_opg(manager, release_proxy_opg)

        rollup_mock_opg = RollupMock.originate_default(manager).send()
        self.bake_block()
        rollup_mock = RollupMock.create_from_opg(manager, rollup_mock_opg)

        router_opg = Router.originate_default(manager).send()
        self.bake_block()
        router = Router.create_from_opg(manager, router_opg)

        # Tokens deployment:
        token_balances = {
            pkh(account): 1000 for account in self.accs.values()
        }

        fa2_opg = FA2.originate(manager, token_balances).send()
        self.bake_block()
        fa2 = FA2.create_from_opg(manager, fa2_opg)

        # Deploying Ticketer with external metadata:
        fa2_external_metadata = {
            'decimals': pack(12, 'nat'),
            'symbol': pack('TEST', 'string'),
        }

        opg = Ticketer.originate(manager, fa2, fa2_external_metadata).send()
        self.bake_block()
        ticketer = Ticketer.create_from_opg(manager, opg)

        opg = TicketHelper.originate(
            client=manager,
            rollup=f'{rollup_mock.address}%rollup',
            token=fa2,
            ticketer=ticketer.address,
            approve_amount=0,
        ).send()
        self.bake_block()
        ticket_helper = TicketHelper.create_from_opg(manager, opg)

        # Ticket Helper gives approval to the Ticketer for the FA2 token:
        ticket_helper.contract.approve().send()
        self.bake_block()

        self.contracts: Contracts = {
            'deposit_proxy': deposit_proxy,
            'release_proxy': release_proxy,
            'rollup_mock': rollup_mock,
            'fa2': fa2,
            'ticketer': ticketer,
            'ticket_helper': ticket_helper,
            'router': router,
        }

        # Ticketer has no tickets and no tokens:
        with self.assertRaises(KeyError):
            fa2.get_balance(ticketer.address)
        assert len(rollup_mock.get_tickets()) == 0
