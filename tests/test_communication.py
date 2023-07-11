from tests.base import BaseTestCase
from scripts.utility import pkh


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        self.fa2.allow(self.ticketer.address).send()
        self.bake_block()

        self.ticketer.deposit(self.fa2, 100).send()
        self.bake_block()
        assert self.fa2.get_balance(self.ticketer.address) == 100

        # TODO:
        # 1. create ticket with ticketer
        # 2. prepare proxy with data
        # 3. send ticket via proxy to the locker

        # check that ticket is locked in the locker