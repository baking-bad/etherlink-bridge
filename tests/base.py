from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeAutoBakeTestCase
from scripts.helpers import Ticketer#, Proxy, Locker


class BaseTestCase(SandboxedNodeAutoBakeTestCase):

    def activate_accs(self) -> None:
        self.user = self.client.using(key='bootstrap1')
        self.user.reveal()

        self.manager = self.client.using(key='bootstrap4')
        self.manager.reveal()


    def setUp(self) -> None:
        self.TIME_BETWEEN_BLOCKS = 1
        self.activate_accs()

        self.ticketer = Ticketer.deploy_default(self.client)
        # TODO: deploy other contracts
        # self.deploy_proxy(self.client)
        # self.deploy_locker(self.client)
