from tests.base import BaseTestCase
from tests.utility import pkh


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        assert self.fa2.get_balance(self.ticketer.address) == 0
        assert len(self.locker.get_tickets()) == 0

        ticket_params = self.ticketer.make_ticket_transfer_params(
            token=self.fa2,
            amount=25,
            destination=self.proxy.address,
            entrypoint='send_ticket',
        )

        self.manager.bulk(
            self.fa2.allow(self.ticketer.address),
            self.ticketer.deposit(self.fa2, 100),
            self.proxy.set({
                'data': pkh(self.manager),
                'receiver': self.locker.address,
            }),
            self.manager.transfer_ticket(**ticket_params),
        ).send()

        self.bake_block()

        # TODO: improve this check and make sure ticket payload and amount is correct
        assert len(self.locker.get_tickets()) == 1
        assert self.fa2.get_balance(self.ticketer.address) == 100
        # TODO: check tickets count in locker and manager addresses

        # TODO: release ticket
