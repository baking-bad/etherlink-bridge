from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeTestCase
from tests.helpers.contracts import (
    Ticketer,
    ProxyRouter,
    ProxyTicketer,
    RollupMock,
    FA2,
    ContractHelper,
    Router,
)
from tests.helpers.utility import pkh
from typing import Type, TypeVar


class BaseTestCase(SandboxedNodeTestCase):

    def activate_accs(self) -> None:
        # TODO: consider adding some Account abstraction with `address` property
        self.alice = self.client.using(key='bootstrap1')
        self.alice.reveal()

        self.boris = self.client.using(key='bootstrap2')
        self.boris.reveal()

        self.manager = self.client.using(key='bootstrap4')
        self.manager.reveal()


    def setUp(self) -> None:
        self.activate_accs()

        # Contracts deployment:
        T = TypeVar('T', bound='ContractHelper')
        def deploy_contract(cls: Type[T]) -> T:
            opg = cls.originate_default(self.manager).send()
            self.bake_block()
            return cls.create_from_opg(self.manager, opg)

        self.ticketer = deploy_contract(Ticketer)
        self.proxy_router = deploy_contract(ProxyRouter)
        self.proxy_ticketer = deploy_contract(ProxyTicketer)
        self.rollup_mock = deploy_contract(RollupMock)
        self.router = deploy_contract(Router)

        # Tokens deployment:
        token_balances = {
            pkh(self.alice): 1000,
            pkh(self.boris): 1000,
            pkh(self.manager): 1000,
            self.ticketer.address: 0,
            self.proxy_router.address: 0,
            self.proxy_ticketer.address: 0,
            self.rollup_mock.address: 0,
        }

        fa2_opg = FA2.originate(self.manager, token_balances).send()
        self.bake_block()
        self.fa2 = FA2.create_from_opg(self.manager, fa2_opg)
