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
        T = TypeVar('T', bound='ContractHelper')
        def deploy_contract(cls: Type[T]) -> T:
            opg = cls.originate_default(manager).send()
            self.bake_block()
            return cls.create_from_opg(manager, opg)

        deposit_proxy = deploy_contract(DepositProxy)
        release_proxy = deploy_contract(ReleaseProxy)
        rollup_mock = deploy_contract(RollupMock)
        router = deploy_contract(Router)

        # Tokens deployment:
        token_balances = {
            pkh(account): 1000 for account in self.accs.values()
        }

        fa2_opg = FA2.originate(manager, token_balances).send()
        self.bake_block()
        fa2 = FA2.create_from_opg(manager, fa2_opg)

        # Deploying Ticketer with external metadata:
        fa2_key = ( "fa2", ( fa2.address, 0 ) )
        fa2_external_metadata = {
            'decimals': pack(12, 'nat'),
            'symbol': pack('TEST', 'string'),
        }

        opg = Ticketer.originate_with_external_metadata(
            manager,
            external_metadata={
                fa2_key: fa2_external_metadata
            },
        ).send()
        self.bake_block()
        ticketer = Ticketer.create_from_opg(manager, opg)

        self.contracts: Contracts = {
            'deposit_proxy': deposit_proxy,
            'release_proxy': release_proxy,
            'rollup_mock': rollup_mock,
            'fa2': fa2,
            'ticketer': ticketer,
            'router': router,
        }

        # Ticketer has no tickets and no tokens:
        with self.assertRaises(KeyError):
            fa2.get_balance(ticketer.address)
        assert len(rollup_mock.get_tickets()) == 0
