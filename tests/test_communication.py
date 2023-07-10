from tests.base import BaseTestCase


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        # TEMPORAL: make sure that deployment succeed
        assert self.ticketer is not None
        assert self.proxy is not None
        assert self.locker is not None

        # TODO:
        # 1. create ticket with ticketer
        # 2. prepare proxy with data
        # 3. send ticket via proxy to the locker

        # check that ticket is locked in the locker