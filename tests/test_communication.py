from tests.base import BaseTestCase
from scripts.utility import pkh


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        self.fa2.allow(self.ticketer.address).send()
        self.bake_block()

        # TODO: make a helper for Ticketer to simplify deposit
        opg = self.ticketer.contract.deposit((
            {'fa2': (self.fa2.contract.address, 0)},
            100
        )).send()
        self.bake_block()

        # check token transfered:
        # TODO: get some balance_of helper for FA2:
        key = (self.ticketer.address, 0)
        amount = self.fa2.contract.storage['ledger'][key]()  # type: ignore
        assert amount == 100

        # TODO:
        # 1. create ticket with ticketer
        # 2. prepare proxy with data
        # 3. send ticket via proxy to the locker

        # check that ticket is locked in the locker