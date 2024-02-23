from tezos.tests.base import BaseTestCase
from tezos.tests.helpers.utility import (
    pkh,
    pack,
)


class RollupCommunicationTestCase(BaseTestCase):
    def test_should_be_able_to_deposit_and_withdraw(self) -> None:
        # Deploying contracts:
        boris = self.bootstrap_account()
        alice = self.bootstrap_account()
        token = self.deploy_fa2(balances={pkh(alice): 1000})
        rollup_mock = self.deploy_rollup_mock()
        extra_metadata = {
            'decimals': pack(12, 'nat'),
            'symbol': pack('FA2', 'string'),
        }
        ticketer = self.deploy_ticketer(token, extra_metadata)
        erc_proxy = bytes.fromhex('0101010101010101010101010101010101010101')
        helper = self.deploy_ticket_helper(token, ticketer, erc_proxy)
        ticket = ticketer.get_ticket()
        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')

        # In order to deposit token to the rollup, in one bulk operation:
        # - TicketHelper allowed to transfer tokens from Alice,
        # - Alice locks token on Ticketer and then transfer ticket
        # to the Rollup via TicketHelper contract.
        rollup = f'{rollup_mock.address}%rollup'
        alice.bulk(
            token.allow(pkh(alice), helper.address),
            helper.deposit(rollup, alice_l2_address, 100),
        ).send()
        self.bake_block()

        # Checking deposit operations results:
        assert ticket.get_balance(rollup_mock.address) == 100
        assert token.get_balance(ticketer.address) == 100
        assert ticket.get_balance(pkh(alice)) == 0

        # Then some interactions on L2 leads to outbox message creation:
        # for example Alice send some L2 tokens to Boris and Boris decided
        # to bridge 5 of them back to L1.

        # To withdraw tokens from the rollup, someone should execute outbox
        # message, which would call ticketer contract to burn tickets and
        # transfer tokens to the Boris address:
        rollup_mock.execute_outbox_message(
            {
                'ticket_id': {
                    'ticketer': ticket.ticketer,
                    'token_id': 0,
                },
                'amount': 5,
                'receiver': pkh(boris),
                'router': ticketer.address,
            }
        ).send()
        self.bake_block()

        # Checking withdraw operations results:
        assert ticket.get_balance(rollup_mock.address) == 95
        assert token.get_balance(pkh(boris)) == 5
