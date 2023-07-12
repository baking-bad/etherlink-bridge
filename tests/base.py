from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeAutoBakeTestCase
from tests.helpers import Ticketer, Proxy, Locker, FA2
from tests.utility import pkh


class BaseTestCase(SandboxedNodeAutoBakeTestCase):

    def activate_accs(self) -> None:
        # TODO: consider adding some Account abstraction with `address` property
        self.user = self.client.using(key='bootstrap1')
        self.user.reveal()

        self.manager = self.client.using(key='bootstrap4')
        self.manager.reveal()


    def setUp(self) -> None:
        self.TIME_BETWEEN_BLOCKS = 1
        self.activate_accs()

        self.ticketer = Ticketer.deploy_default(self.manager)
        self.proxy = Proxy.deploy_default(self.manager)
        self.locker = Locker.deploy_default(self.manager)

        fa2_balances = {
            pkh(self.user): 1000,
            pkh(self.manager): 1000,
        }
        self.fa2 = FA2.deploy(self.manager, fa2_balances)
