from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeTestCase
from tests.helpers.contracts import (
    Ticketer,
    ProxyRouterL1Deposit,
    ProxyRouterL2Burn,
    ProxyTicketer,
    RollupMock,
    FA2,
    ContractHelper,
)
from tests.helpers.utility import pkh, pack
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

        self.proxy_l1_deposit = deploy_contract(ProxyRouterL1Deposit)
        self.proxy_ticketer = deploy_contract(ProxyTicketer)
        self.proxy_l2_burn = deploy_contract(ProxyRouterL2Burn)
        self.rollup_mock = deploy_contract(RollupMock)

        # Tokens deployment:
        token_balances = {
            pkh(self.alice): 1000,
            pkh(self.boris): 1000,
            pkh(self.manager): 1000,
        }

        fa2_opg = FA2.originate(self.manager, token_balances).send()
        self.bake_block()
        self.fa2 = FA2.create_from_opg(self.manager, fa2_opg)

        # Deploying Ticketer with external metadata:
        fa2_key = ( "fa2", ( self.fa2.address, 0 ) )
        fa2_external_metadata = {
            'decimals': pack(12, 'nat'),
            'symbol': pack('TEST', 'string'),
        }

        opg = Ticketer.originate_with_external_metadata(
            self.manager,
            external_metadata={
                fa2_key: fa2_external_metadata
            },
        ).send()
        self.bake_block()
        self.ticketer = Ticketer.create_from_opg(self.manager, opg)
