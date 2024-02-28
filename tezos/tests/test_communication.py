from tezos.tests.base import BaseTestCase
from tezos.tests.helpers.utility import pack


class RollupCommunicationTestCase(BaseTestCase):
    def test_should_be_able_to_deposit_and_withdraw(self) -> None:
        boris = self.bootstrap_account()
        alice = self.bootstrap_account()

        alice, token, ticketer, _ = self.default_setup(
            token_type='FA2',
            balance=1000,
            extra_metadata={
                'decimals': pack(12, 'nat'),
                'symbol': pack('FA2', 'string'),
            },
        )
        erc_proxy = bytes.fromhex('fa02fa02fa02fa02fa02fa02fa02fa02fa02fa02')
        helper = self.deploy_ticket_helper(token, ticketer, erc_proxy)
        rollup_mock = self.deploy_rollup_mock()
        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')

        # In order to deposit token to the rollup, in one bulk operation:
        # - TicketHelper allowed to transfer tokens from Alice,
        # - Alice locks token on Ticketer and then transfer ticket
        # to the Rollup via TicketHelper contract.
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
