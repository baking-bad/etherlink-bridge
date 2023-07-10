from tests.base import BaseTestCase
from scripts.utility import pkh


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        # TODO: make a helper for FA2 contract to simplify approve
        self.fa2.contract.update_operators([{
            'add_operator': {
                'owner': pkh(self.manager),
                'operator': self.ticketer.contract.address,
                'token_id': 0
            }
        }]).send()
        self.bake_block()

        # TODO: make a helper for Ticketer to simplify deposit
        opg = self.ticketer.contract.deposit((
            {'fa2': (self.fa2.contract.address, 0)},
            100
        )).send()
        self.bake_block()

        # check token transfered:
        amount = self.fa2.contract.storage['ledger'][(self.ticketer.contract.address, 0)]()
        assert amount == 100

        # TODO:
        # 1. create ticket with ticketer
        # 2. prepare proxy with data
        # 3. send ticket via proxy to the locker

        # check that ticket is locked in the locker