from tests.base import BaseTestCase
from tests.utility import pkh


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        # TODO: make a batch call with all operations
        self.fa2.allow(self.ticketer.address).send()
        self.bake_block()

        self.ticketer.deposit(self.fa2, 100).send()
        self.bake_block()
        assert self.fa2.get_balance(self.ticketer.address) == 100

        self.proxy.set({
            'data': pkh(self.manager),
            'receiver': self.locker.address,
        }).send()
        self.bake_block()

        assert len(self.locker.get_tickets()) == 0

        ticket_params = self.ticketer.make_ticket_transfer_params(
            token=self.fa2,
            amount=25,
            destination=self.proxy.address,
            entrypoint='send_ticket',
        )

        self.manager.transfer_ticket(**ticket_params).send()
        self.bake_block()

        # TODO: improve this check and make sure ticket payload and amount is correct
        assert len(self.locker.get_tickets()) == 1

        # TODO: release ticket
