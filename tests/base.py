from pytezos.client import PyTezosClient
from pytezos.sandbox.node import SandboxedNodeAutoBakeTestCase
from scripts.contracts import ContractHelper


class BaseTestCase(SandboxedNodeAutoBakeTestCase):

    def activate_accs(self) -> None:
        self.user = self.client.using(key='bootstrap1')
        self.user.reveal()

        self.manager = self.client.using(key='bootstrap4')
        self.manager.reveal()

    def deploy_ticketer(self, client: PyTezosClient) -> ContractHelper:
        """Deploys Ticketer with empty storage"""

        # TODO: consider making helper function to generate storage
        # OR: consider moving this to the Contract class as default_storage
        storage = {
            'extra_metadata': {},
            'metadata': {},
            'token_ids': {},
            'next_token_id': 0,
        }

        return ContractHelper.deploy_from_build('ticketer', client, storage)

    def setUp(self) -> None:
        self.TIME_BETWEEN_BLOCKS = 1
        self.activate_accs()
        self.ticketer = self.deploy_ticketer(self.client)
        # TODO: self.ticketer = Ticketer.deploy_default(self.client)
        # TODO: deploy other contracts
        # self.deploy_proxy(self.client)
        # self.deploy_locker(self.client)
