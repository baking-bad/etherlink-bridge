from tests.base import BaseTestCase
from tests.helpers.routing_data import create_routing_data
from tests.helpers.utility import (
    pkh,
    pack,
)
from tests.helpers.tickets import (
    get_all_ticket_balances_by_ticketer,
    get_ticket_balance,
    create_expected_ticket,
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
        transfer_params = self.ticketer.make_ticket_transfer_params(
            token=self.fa2,
            amount=25,
            destination=self.proxy_router.address,
            entrypoint='send_ticket',
        )

        # Here we create routing data for the proxy contract that will
        # create "L2" ticket in the Rollup contract for Alice:
        routing_data = create_routing_data(
            refund_address=pkh(self.alice),
            l2_address=pkh(self.alice),
        )

        # Then in one bulk we allow ticketer to transfer tokens,
        # deposit tokens to the ticketer, set routing info to the proxy
        # and transfer ticket to the Rollup (Locker) by sending created ticket
        # to the proxy contract, which will send it to the Rollup with routing info:
        self.alice.bulk(
            self.fa2.using(self.alice).allow(self.ticketer.address),
            self.ticketer.using(self.alice).deposit(self.fa2, 100),
            self.proxy_router.using(self.alice).set({
                'data': routing_data,
                'receiver': f'{self.rollup_mock.address}%save',
            }),
            self.alice.transfer_ticket(**transfer_params),
        ).send()

        self.bake_block()

        # Checking operations results:
        # 1. Rollup has L1 tickets:
        expected_l1_ticket = create_expected_ticket(
            ticketer=self.ticketer.address,
            token_id=0,
            token=self.fa2,
        )
        balance = get_ticket_balance(
            self.client,
            expected_l1_ticket,
            self.rollup_mock.address,
        )
        self.assertEqual(balance, 25)

        # 2. Ticketer has FA2 tokens:
        assert self.fa2.get_balance(self.ticketer.address) == 100

        # 3. Alice has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            expected_l1_ticket,
            pkh(self.alice),
        )
        self.assertEqual(balance, 75)

        # 4. Alice has L2 tickets:
        expected_l2_ticket = create_expected_ticket(
            ticketer=self.rollup_mock.address,
            token_id=0,
            token=self.fa2,
        )
        balance = get_ticket_balance(
            self.client,
            expected_l2_ticket,
            pkh(self.alice),
        )
        self.assertEqual(balance, 25)

        # Transfer some L2 tickets to Boris's address
        self.alice.transfer_ticket(
            ticket_contents=expected_l2_ticket['content'],
            ticket_ty=expected_l2_ticket['content_type'],
            ticket_ticketer=expected_l2_ticket['ticketer'],
            ticket_amount=10,
            destination=pkh(self.boris),
        ).send()
        self.bake_block()

        # Boris burns some L2 tickets to get L1 tickets back:
        self.boris.transfer_ticket(
            ticket_contents=expected_l2_ticket['content'],
            ticket_ty=expected_l2_ticket['content_type'],
            ticket_ticketer=expected_l2_ticket['ticketer'],
            ticket_amount=5,
            destination=self.rollup_mock.address,
            entrypoint='l2_burn',
        ).send()
        self.bake_block()

        # Checking that L2 burn created outbox message:
        outbox_message = self.rollup_mock.get_message(0)
        self.assertEqual(outbox_message['receiver'], pkh(self.boris))
        self.assertEqual(outbox_message['amount'], 5)

        # Anyone can trigger outbox message:
        self.rollup_mock.release(0).send()
        self.bake_block()

        # Boris should have now L1 tickets too:
        balance = get_ticket_balance(
            self.client,
            expected_l1_ticket,
            pkh(self.boris),
        )
        self.assertEqual(balance, 5)

        # Rollup should have some L2 tickets left:
        balance = get_ticket_balance(
            self.client,
            expected_l1_ticket,
            self.rollup_mock.address,
        )
        self.assertEqual(balance, 20)

        # Boris unpacks some L1 tickets to get back some FA2 tokens
        self.boris.bulk(
            self.proxy_ticketer.using(self.boris).set({
                'data': pkh(self.boris),
                'receiver': f'{self.ticketer.address}%release',
            }),
            self.boris.transfer_ticket(
                ticket_contents=expected_l1_ticket['content'],
                ticket_ty=expected_l1_ticket['content_type'],
                ticket_ticketer=expected_l1_ticket['ticketer'],
                ticket_amount=2,
                destination=self.proxy_ticketer.address,
                entrypoint='send_ticket',
            )
        ).send()
        self.bake_block()

        # Boris should have burned some L1 tickets:
        balance = get_ticket_balance(
            self.client,
            expected_l1_ticket,
            pkh(self.boris),
        )
        self.assertEqual(balance, 3)

        # TODO: check Boris should have some FA2 tokens now

    # TODO: test_should_return_ticket_to_sender_if_wrong_payload
    # TODO: test_minted_ticket_should_have_expected_content_and_type

    # TODO: ? multiple users add same tickets to rollup mock
    # TODO: ? different tickets from one ticketer
