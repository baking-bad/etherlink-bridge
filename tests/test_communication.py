from tests.base import BaseTestCase
from tests.helpers.proxy import RoutingData
from tests.utility import (
    pkh,
    pack,
)
from typing import cast


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        # Bridging FA2 / FA1.2 token includes next steps:
        # 1. Allow ticketer to transfer tokens
        # 2. Make ticket from tokens by depositing them to the ticketer
        # 3. Transfer tickets to the Rollup (which is represeented by Locker)
        #    - as far as implicit address can't send tickets with extra data
        #      we use special proxy contract to do this

        # First we check that ticketer has no tickets and no tokens:
        assert self.fa2.get_balance(self.ticketer.address) == 0
        assert len(self.rollup_mock.get_tickets()) == 0

        # Then we configure ticket transfer params and routing info:
        ticket_params = self.ticketer.make_ticket_transfer_params(
            token=self.fa2,
            amount=25,
            destination=self.proxy.address,
            entrypoint='send_ticket',
        )

        # TODO: consider creating special helper for RoutingData
        # Here we create routing data for the proxy contract that will
        # create "L2" ticket in the Rollup (Locker) contract for manager:
        manager_address = pkh(self.manager)
        routing_data = cast(RoutingData, {
            'data': pack(manager_address, 'address'),
            'refund_address': manager_address,
            'info': {
                'routing_type': pack('to_l2_address', 'string'),
                'data_type': pack('address', 'string'),
                'version': pack('0.1.0', 'string'),
            }
        })

        # Then in one bulk we allow ticketer to transfer tokens,
        # deposit tokens to the ticketer, set routing info to the proxy
        # and transfer ticket to the Rollup (Locker) by sending created ticket
        # to the proxy contract, which will send it to the Rollup with routing info:
        self.manager.bulk(
            self.fa2.allow(self.ticketer.address),
            self.ticketer.deposit(self.fa2, 100),
            self.proxy.set({
                'data': routing_data,
                'receiver': self.rollup_mock.address,
            }),
            self.manager.transfer_ticket(**ticket_params),
        ).send()

        self.bake_block()

        # Finally we check that locker (Rollup) has tickets and ticketer has tokens:
        # TODO: improve this check and make sure ticket payload and amount is correct
        assert len(self.rollup_mock.get_tickets()) == 1
        assert self.fa2.get_balance(self.ticketer.address) == 100
        # TODO: check tickets count in locker and manager addresses
        # TODO: check that L2 ticket created

        # TODO: release ticket

    # TODO: test_should_return_ticket_to_sender_if_wrong_payload
