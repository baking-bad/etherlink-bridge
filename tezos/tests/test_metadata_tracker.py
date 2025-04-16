from tezos.tests.base import BaseTestCase
from scripts.helpers.contracts.metadata_tracker import MetadataTracker
from scripts.helpers.utility import find_op_by_hash


class MetadataTrackerTestCase(BaseTestCase):
    def deploy_metadata_tracker(self) -> MetadataTracker:
        """Deploys MetadataTracker contract"""

        opg = MetadataTracker.originate(self.manager).send()
        self.bake_block()
        return MetadataTracker.from_opg(self.manager, opg)

    def test_should_allow_to_post_metadata_and_does_nothing(self) -> None:
        alice = self.bootstrap_account()
        metadata_tracker = self.deploy_metadata_tracker()

        bytes_message = (123456789).to_bytes(8, 'big')
        opg = metadata_tracker.using(alice).default(bytes_message).send()
        self.bake_block()

        result = find_op_by_hash(alice, opg)
        metadata_in_opg = result['contents'][0]['parameters']['value']['bytes']
        assert bytes_message.hex() == metadata_in_opg
