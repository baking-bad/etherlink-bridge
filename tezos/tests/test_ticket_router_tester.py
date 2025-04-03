from tezos.tests.base import BaseTestCase
from scripts.helpers.ticket_content import TicketContent
from scripts.helpers.ticket import Ticket


class TicketerRouterTesterTestCase(BaseTestCase):
    def test_should_allow_to_deposit_to_the_rollup_without_erc_proxy(self) -> None:
        alice, token, ticketer, tester = self.default_setup('FA2')
        rollup_mock = self.deploy_rollup_mock()

        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')
        alice.bulk(
            token.allow(alice, ticketer),
            ticketer.deposit(100),
        ).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 100

        alice.bulk(
            tester.set_rollup_deposit(
                target=f'{rollup_mock.address}%rollup',
                routing_info=alice_l2_address,
            ),
            ticket.transfer(tester),
        ).send()
        self.bake_block()
        assert ticketer.read_ticket(rollup_mock).amount == 100

    def test_should_redirect_ticket_to_receiver_when_called_on_withdraw_entry(
        self,
    ) -> None:
        alice = self.bootstrap_account()
        bonita = self.bootstrap_account()
        tester = self.deploy_ticket_router_tester()
        rollup_mock = self.deploy_rollup_mock()

        content = TicketContent(42, None)

        # mint tickets to the RollupMock contract:
        alice.bulk(
            tester.set_rollup_deposit(
                target=f'{rollup_mock.address}%rollup',
                routing_info=bytes.fromhex('00' * 20),
            ),
            tester.mint(content, 99),
        ).send()
        self.bake_block()

        ticket = Ticket.create(alice, rollup_mock, tester.address, content)
        assert ticket.amount == 99

        # send the ticket to the tester contract:
        # NOTE: bonita should be ignored and alice should receive the ticket
        alice.bulk(
            tester.set_default(target=bonita),
            rollup_mock.execute_outbox_message(
                {
                    'ticket_id': {
                        'token_id': 42,
                        'ticketer': tester,
                    },
                    'amount': 18,
                    'receiver': alice,
                    'router': tester,
                }
            ),
        ).send()
        self.bake_block()

        # check that the ticket was transferred to alice:
        client = alice
        ticket = Ticket.create(client, alice, tester.address, content)
        assert ticket.amount == 18

        ticket = Ticket.create(client, bonita, tester.address, content)
        assert ticket.amount == 0

        ticket = Ticket.create(client, rollup_mock, tester.address, content)
        assert ticket.amount == 99 - 18
