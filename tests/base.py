from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeTestCase
from tests.helpers.contracts import Ticketer, Proxy, RollupMock, FA2
from tests.helpers.utility import pkh


class BaseTestCase(SandboxedNodeTestCase):

    def activate_accs(self) -> None:
        # TODO: consider adding some Account abstraction with `address` property
        self.user = self.client.using(key='bootstrap1')
        self.user.reveal()

        self.manager = self.client.using(key='bootstrap4')
        self.manager.reveal()


    def setUp(self) -> None:
        self.activate_accs()

        # Contracts deployment:
        ticketer_opg = Ticketer.originate_default(self.manager).send()
        self.bake_block()
        self.ticketer = Ticketer.create_from_opg(self.manager, ticketer_opg)

        proxy_opg = Proxy.originate_default(self.manager).send()
        self.bake_block()
        self.proxy = Proxy.create_from_opg(self.manager, proxy_opg)

        rollup_mock_opg = RollupMock.originate_default(self.manager).send()
        self.bake_block()
        self.rollup_mock = RollupMock.create_from_opg(self.manager, rollup_mock_opg)

        # Tokens deployment:
        token_balances = {
            pkh(self.user): 1000,
            pkh(self.manager): 1000,
            self.ticketer.address: 0,
            self.proxy.address: 0,
            self.rollup_mock.address: 0,
        }

        fa2_opg = FA2.originate(self.manager, token_balances).send()
        self.bake_block()
        self.fa2 = FA2.create_from_opg(self.manager, fa2_opg)
