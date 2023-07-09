from pytezos.client import PyTezosClient
from pytezos.contract.interface import ContractInterface
from pytezos.sandbox.node import SandboxedNodeTestCase
from scripts.utility import (
    deploy_contract_with_storage,
    load_contract_from_opg
)
from scripts.contracts import (
    TICKETER,
    PROXY,
    LOCKER,
)


class BaseTestCase(SandboxedNodeTestCase):

    def activate_accs(self) -> None:
        self.user = self.client.using(key='bootstrap1')
        self.user.reveal()

        self.manager = self.client.using(key='bootstrap4')
        self.manager.reveal()

    def deploy_ticketer(self, client: PyTezosClient) -> ContractInterface:
        """Deploys Ticketer with empty storage"""

        # TODO: consider making helper function to generate storage
        # OR: consider moving this to the Contract class as default_storage
        storage = {
            'extra_metadata': {},
            'metadata': {},
            'token_ids': {},
            'next_token_id': 0,
        }

        contract = TICKETER.contract.using(shell=client.shell, key=client.key)
        opg = contract.originate(initial_storage=storage)
        result = opg.send()
        self.bake_block()

        return load_contract_from_opg(client, result)

        # Alternative implementation reusing deploy function:
        # (does not work because it is required to call self.bake_block())
        """
        contract_address = deploy_contract_with_storage(client, TICKETER, storage)
        return contract_address
        """

    def setUp(self) -> None:
        self.activate_accs()
        self.ticketer = self.deploy_ticketer(self.client)
        # TODO: deploy other contracts
        # self.deploy_proxy(self.client)
        # self.deploy_locker(self.client)
