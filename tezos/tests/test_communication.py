from tezos.tests.base import BaseTestCase


class RollupCommunicationTestCase(BaseTestCase):
    def test_should_be_able_to_deposit_and_withdraw(self) -> None:
        boris = self.bootstrap_account()
        alice = self.bootstrap_account()

        alice, token, ticketer, _ = self.default_setup(
            token_type='FA2',
            balance=1000,
            extra_metadata={
                'decimals': '12',
                'symbol': 'FA2',
            },
        )
        erc_proxy = bytes.fromhex('fa02fa02fa02fa02fa02fa02fa02fa02fa02fa02')
        helper = self.deploy_token_bridge_helper(token, ticketer, erc_proxy)
        rollup_mock = self.deploy_rollup_mock()
        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')

        # In order to deposit token to the rollup, in one bulk operation:
        # - TokenBridgeHelper allowed to transfer tokens from Alice,
        # - Alice locks token on Ticketer and then transfer ticket
        # to the Rollup via TokenBridgeHelper contract.
        rollup = f'{rollup_mock.address}%rollup'
        alice.bulk(
            token.allow(alice, helper),
            helper.deposit(rollup, alice_l2_address, 100),
        ).send()
        self.bake_block()

        # Checking deposit operations results:
        assert ticketer.read_ticket(alice).amount == 0
        assert ticketer.read_ticket(rollup_mock).amount == 100
        assert token.get_balance(ticketer) == 100

        # Then some interactions on L2 leads to outbox message creation:
        # for example Alice send some L2 tokens to Boris and Boris decided
        # to bridge 5 of them back to L1.

        # To withdraw tokens from the rollup, someone should execute outbox
        # message, which would call ticketer contract to burn tickets and
        # transfer tokens to the Boris address:
        rollup_mock.execute_outbox_message(
            {
                'ticket_id': {
                    'ticketer': ticketer,
                    'token_id': 0,
                },
                'amount': 5,
                'receiver': boris,
                'router': ticketer,
            }
        ).send()
        self.bake_block()

        # Checking withdraw operations results:
        assert ticketer.read_ticket(rollup_mock).amount == 95
        assert token.get_balance(boris) == 5

    def test_create_and_burn_multuple_tickets_from_different_users(self) -> None:
        alice = self.bootstrap_account()
        boris = self.bootstrap_account()
        token = self.deploy_fa2(
            {
                alice: 1000,
                boris: 1000,
            }
        )
        ticketer = self.deploy_ticketer(token)
        helper = self.deploy_token_bridge_helper(token, ticketer)

        # Alice creates one ticket from 5 tokens:
        alice.bulk(
            token.allow(alice, ticketer),
            ticketer.deposit(5),
        ).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 5
        assert token.get_balance(ticketer) == 5

        # Alice burns 2 tickets:
        burned_ticket, remaining_ticket = ticket.split(2)
        burned_ticket.transfer(helper, 'unwrap').send()
        self.bake_block()

        assert token.get_balance(ticketer) == 3

        # Alice transfers 2 tickets to Boris:
        transferred_ticket, remaining_ticket = remaining_ticket.split(2)
        transferred_ticket.transfer(boris).send()
        self.bake_block()

        assert ticketer.read_ticket(alice).amount == 1
        assert ticketer.read_ticket(boris).amount == 2
        assert ticketer.get_total_supply_view() == 3

        # Boris creates 1 more ticket:
        boris.bulk(
            token.allow(boris, ticketer),
            ticketer.deposit(1),
        ).send()
        self.bake_block()

        boris_ticket = ticketer.read_ticket(boris)
        assert boris_ticket.amount == 3
        assert ticketer.get_total_supply_view() == 4

        # Boris burns 3 tickets:
        boris_ticket.transfer(helper, 'unwrap').send()
        self.bake_block()

        assert ticketer.read_ticket(boris).amount == 0
        assert ticketer.get_total_supply_view() == 1
