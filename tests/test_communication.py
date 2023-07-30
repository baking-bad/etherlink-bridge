from tests.base import BaseTestCase
from tests.helpers.routing_data import create_routing_data
from tests.helpers.utility import (
    pkh,
    pack,
)
from tests.helpers.tickets import (
    get_all_ticket_balances_by_ticketer,
    get_ticket_balance,
)


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

        # Here we create routing data for the proxy contract that will
        # create "L2" ticket in the Rollup (Locker) contract for manager:
        manager_address = pkh(self.manager)
        routing_data = create_routing_data(
            refund_address=manager_address,
            l2_address=manager_address,
        )

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

        # Checking operations results:
        # 1. Rollup has L1 tickets:
        rollup_tickets = self.rollup_mock.get_tickets()
        assert len(rollup_tickets) == 1
        ticket = rollup_tickets[0]
        self.assertEqual(ticket['ticketer'], self.ticketer.address)
        self.assertEqual(ticket['amount'], 25)

        # 2. Ticketer has FA2 tokens:
        assert self.fa2.get_balance(self.ticketer.address) == 100

        # 3. Manager has L1 tickets:
        # TODO: add some test CONSTs with ticket CONTENT_TYPE and CONTENT
        l1_tickets_amount = get_ticket_balance(
            self.client,
            pkh(self.manager),
            self.ticketer.address,
            ticket['content_type'],
            ticket['content'],
        )
        assert l1_tickets_amount == 75

        # 4. Manager has L2 tickets:
        l2_tickets_amount = get_ticket_balance(
            self.client,
            pkh(self.manager),
            self.rollup_mock.address,
            ticket['content_type'],
            ticket['content'],
        )
        assert l2_tickets_amount == 25

        # Transfer some L2 tickets to another address
        # TODO: burn some L2 tickets to get L1 tickets back on another address
        # TODO: unpack L1 tickets to get back FA2 tokens

    # TODO: test_should_return_ticket_to_sender_if_wrong_payload
    # TODO: test_minted_ticket_should_have_expected_content_and_type

    # TODO: ? multiple users add same tickets to rollup mock
    # TODO: ? different tickets from one ticketer
