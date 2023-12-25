from tezos.tests.base import BaseTestCase
from tezos.tests.helpers.utility import (
    pkh,
    pack,
)
from tezos.tests.helpers.tickets import get_all_by_ticketer


class RollupCommunicationTestCase(BaseTestCase):
    def test_should_be_able_to_deposit_and_withdraw(self) -> None:
        # Deploying contracts:
        boris = self.bootstrap_account()
        alice = self.bootstrap_account()
        token = self.deploy_fa2(balances={pkh(alice): 1000})
        rollup_mock = self.deploy_rollup_mock()
        router = self.deploy_router()
        extra_metadata = {
            'decimals': pack(12, 'nat'),
            'symbol': pack('FA2', 'string'),
        }
        ticketer = self.deploy_ticketer(token, extra_metadata)
        helper = self.deploy_ticket_helper(token, ticketer)
        ticket = ticketer.get_ticket()

        # There are two addresses on L2, the first one is ERC20 proxy contract,
        # which would receve L2 tickets and the second is the Alice L2 address,
        # which would receive L2 tokens minted by ERC20 proxy contract:
        token_proxy = bytes.fromhex('0101010101010101010101010101010101010101')
        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')

        # In order to deposit token to the rollup, in one bulk operation:
        # - TicketHelper allowed to transfer tokens from Alice,
        # - Alice locks token on Ticketer and then transfer ticket
        # to the Rollup via TicketHelper contract.
        routing_info = token_proxy + alice_l2_address
        rollup = f'{rollup_mock.address}%rollup'
        alice.bulk(
            token.allow(pkh(alice), helper.address),
            helper.deposit(rollup, routing_info, 100),
        ).send()
        self.bake_block()

        # Checking deposit operations results:
        assert ticket.get_balance(rollup_mock.address) == 100
        assert token.get_balance(ticketer.address) == 100
        assert ticket.get_balance(pkh(alice)) == 0

        # Then some interactions on L2 leads to outbox message creation:
        # for example Alice send some L2 tokens to Boris and Boris decided
        # to bridge 5 of them back to L1.
        rollup_mock.create_outbox_message(
            {
                'ticket_id': {
                    'ticketer': ticket.ticketer,
                    'token_id': 0,
                },
                'amount': 5,
                'routing_data': pack(pkh(boris), 'address'),
                'router': ticketer.address,
            }
        ).send()
        self.bake_block()

        # To withdraw tokens from the rollup, someone should execute outbox
        # message, which would call ticketer contract to burn tickets and
        # transfer tokens to the Boris address:
        rollup_mock.execute_outbox_message(0).send()
        self.bake_block()

        # Checking withdraw operations results:
        assert ticket.get_balance(rollup_mock.address) == 95
        assert token.get_balance(pkh(boris)) == 5
