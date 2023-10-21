from tests.base import BaseTestCase
from tests.helpers.utility import (
    pkh,
    pack,
)
from tests.helpers.tickets import (
    get_all_ticket_balances_by_ticketer,
    get_ticket_balance,
    create_ticket,
)


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        # Bridging FA2 / FA1.2 token includes next steps:
        # 1. Allow ticketer to transfer tokens
        # 2. Make ticket from tokens by depositing them to the ticketer
        # 3. Transfer tickets to the Rollup
        #    - as far as implicit address can't send tickets with extra data
        #      we use special proxy contract to do this

        # TODO: it is probably good idea to remove `self.` from all contracts

        # First we check that ticketer has no tickets and no tokens:
        with self.assertRaises(KeyError):
            self.fa2.get_balance(self.ticketer.address)
        assert len(self.rollup_mock.get_tickets()) == 0

        # TODO: need to create some helper to manage ticket creation / transfers:
        # TODO: need to allow to create token info from token + ticketer
        ticket = create_ticket(
            ticketer=self.ticketer.address,
            token_id=0,
            token_info={
                'contract_address': pack(self.fa2.address, 'address'),
                'token_id': pack(self.fa2.token_id, 'nat'),
                'token_type': pack("FA2", 'string'),
                'decimals': pack(12, 'nat'),
                'symbol': pack('TEST', 'string'),
            },
        )

        # Then in one bulk we allow ticketer to transfer tokens,
        # deposit tokens to the ticketer, set routing info to the proxy
        # and transfer ticket to the Rollup (Locker) by sending created ticket
        # to the proxy contract, which will send it to the Rollup with routing info:
        self.alice.bulk(
            self.fa2.using(self.alice).allow(self.ticketer.address),
            self.ticketer.using(self.alice).deposit(self.fa2, 100),
            self.proxy_deposit.using(self.alice).set({
                'data': 'Alice L2 address'.encode('utf-8'),
                'receiver': f'{self.rollup_mock.address}%deposit',
            }),
            self.alice.transfer_ticket(
                ticket_contents = ticket['content'],
                ticket_ty = ticket['content_type'],
                ticket_ticketer = ticket['ticketer'],
                ticket_amount = 25,
                destination = self.proxy_deposit.address,
                entrypoint = 'send',
            ),
        ).send()

        self.bake_block()

        # Checking operations results:
        # 1. Rollup has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            self.rollup_mock.address,
        )
        self.assertEqual(balance, 25)

        # 2. Ticketer has FA2 tokens:
        assert self.fa2.get_balance(self.ticketer.address) == 100

        # 3. Alice has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(self.alice),
        )
        self.assertEqual(balance, 75)

        # Then some interactions on L2 leads to outbox message creation:
        #    for example Alice send some L2 tokens to Boris and Boris decided
        #    to bridge 5 of them back to L1
        self.rollup_mock.using(self.boris).create_outbox_message({
            'ticket_id': {
                'ticketer': ticket['ticketer'],
                'token_id': 0,
            },
            'amount': 5,
            'routing_data': pack(pkh(self.boris), 'address'),
        }).send()

        self.bake_block()

        # Anyone can trigger outbox message:
        self.rollup_mock.execute_outbox_message(0).send()
        self.bake_block()

        # Boris should have now L1 tickets too:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(self.boris),
        )
        self.assertEqual(balance, 5)

        # Rollup should have some L2 tickets left:
        balance = get_ticket_balance(
            self.client,
            ticket,
            self.rollup_mock.address,
        )
        self.assertEqual(balance, 20)

        # Boris unpacks some L1 tickets to get back some FA2 tokens
        boris_tokens_before_burn = self.fa2.get_balance(pkh(self.boris))

        self.boris.bulk(
            self.proxy_ticketer.using(self.boris).set({
                'data': pkh(self.boris),
                'receiver': f'{self.ticketer.address}%release',
            }),
            self.boris.transfer_ticket(
                ticket_contents=ticket['content'],
                ticket_ty=ticket['content_type'],
                ticket_ticketer=ticket['ticketer'],
                ticket_amount=2,
                destination=self.proxy_ticketer.address,
                entrypoint='send',
            )
        ).send()
        self.bake_block()

        # Boris should have burned some L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(self.boris),
        )
        self.assertEqual(balance, 3)

        # Boris should have more FA2 tokens now:
        boris_tokens_after_burn = self.fa2.get_balance(pkh(self.boris))
        self.assertEqual(
            boris_tokens_after_burn,
            boris_tokens_before_burn + 2
        )

    # TODO: test_should_return_ticket_to_sender_if_wrong_payload
    # TODO: test_minted_ticket_should_have_expected_content_and_type

    # TODO: ? multiple users add same tickets to rollup mock
    # TODO: ? different tickets from one ticketer

    # TODO: test that L2 ticket have correct L1 ticketer address and token id
