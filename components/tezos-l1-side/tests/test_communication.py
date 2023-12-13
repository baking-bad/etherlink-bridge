from tests.base import BaseTestCase
from tests.helpers.utility import (
    pkh,
    pack,
)
from tests.helpers.tickets import (
    get_all_ticket_balances_by_ticketer,
    get_ticket_balance,
)


class RollupCommunicationTestCase(BaseTestCase):
    def test_should_be_able_to_deposit_and_withdraw(self) -> None:
        # TODO: consider split it to two tests: deposit and withdraw
        boris = self.accs['boris']
        alice = self.accs['alice']
        fa2 = self.contracts['fa2']
        deposit_proxy = self.contracts['deposit_proxy']
        release_proxy = self.contracts['release_proxy']
        rollup_mock = self.contracts['rollup_mock']
        ticketer = self.contracts['ticketer']
        router = self.contracts['router']

        ticket = ticketer.get_ticket()

        # There are two addresses on L2, the first one is ERC20 proxy contract,
        # which would receve L2 tickets and the second is the Alice L2 address,
        # which would receive L2 tokens minted by ERC20 proxy contract:
        token_proxy = bytes.fromhex('0101010101010101010101010101010101010101')
        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')

        # In order to deposit token to the rollup, in one bulk operation:
        # - ticketer allowed to transfer tokens from Alice,
        # - Alice calls deposit tokens to the ticketer,
        # - Alice set routing info to the proxy
        #   (as far as implicit address can't send tickets with extra data),
        # - Alice transfer ticket to the Rollup via proxy contract.
        alice.bulk(
            fa2.using(alice).allow(ticketer.address),
            ticketer.using(alice).deposit({'amount': 100}),
            deposit_proxy.using(alice).set({
                'data': token_proxy + alice_l2_address,
                'receiver': f'{rollup_mock.address}%rollup',
            }),
            # TODO: ticket helper may be good here: alice.transfer_ticket(ticket, 25, dest, entry)
            alice.transfer_ticket(
                ticket_contents = ticket['content'],
                ticket_ty = ticket['content_type'],
                ticket_ticketer = ticket['ticketer'],
                ticket_amount = 25,
                destination = deposit_proxy.address,
                entrypoint = 'send',
            ),
        ).send()
        self.bake_block()

        # Checking deposit operations results:
        # - Rollup has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            rollup_mock.address,
        )
        self.assertEqual(balance, 25)

        # - Ticketer has FA2 tokens:
        assert fa2.get_balance(ticketer.address) == 100

        # - Alice has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(alice),
        )
        self.assertEqual(balance, 75)

        # Then some interactions on L2 leads to outbox message creation:
        # for example Alice send some L2 tokens to Boris and Boris decided
        # to bridge 5 of them back to L1.
        rollup_mock.using(boris).create_outbox_message({
            'ticket_id': {
                'ticketer': ticket['ticketer'],
                'token_id': 0,
            },
            'amount': 5,
            'routing_data': pack(pkh(boris), 'address'),
            'router': ticketer.address,
        }).send()
        self.bake_block()

        # To withdraw tokens from the rollup, someone should execute outbox
        # message, which would call ticketer contract to burn tickets and
        # transfer tokens to the Boris address:
        boris_tokens_before_burn = fa2.get_balance(pkh(boris))
        rollup_mock.execute_outbox_message(0).send()
        self.bake_block()

        # Checking withdraw operations results:
        # - Rollup should have some L1 tickets left:
        balance = get_ticket_balance(
            self.client,
            ticket,
            rollup_mock.address,
        )
        self.assertEqual(balance, 20)

        # - Boris should have more FA2 tokens now:
        boris_tokens_after_burn = fa2.get_balance(pkh(boris))
        self.assertEqual(
            boris_tokens_after_burn,
            boris_tokens_before_burn + 5
        )

    '''
    // TODO: this is part of the test above, that was used before
    //       need to split it to several tests:
    //       - Ticketer.test_should_return_fa2_on_withdraw
    //       - Ticketer.test_should_return_fa12_on_withdraw
    //       - Ticketer.test_should_burn_ticket_on_withdraw
    //       - Ticketer.test_should_create_ticket_on_deposit_fa12
    //       - Ticketer.test_should_lock_tokens_on_deposit_fa12
    //       - Ticketer.test_should_create_ticket_on_deposit_fa2
    //       - Ticketer.test_should_lock_tokens_on_deposit_fa2
    //       - Ticketer.test_should_fail_when_withdraw_wrong_ticket
    //       - Ticketer.test_should_add_metadata_to_the_ticket_payload
    //          - probably good to have multiple tests for different metadata setups:
    //          - no additional metadata
    //          - additional metadata for FA2
    //          - additional metadata for FA1.2
    //       - Ticketer.test_should_fail_on_deposit_with_attached_xtz
    //       - Ticketer.test_should_fail_on_withdraw_with_attached_xtz

    //       - Router.test_should_redirect_ticket_on_withdraw_from_rollup
    //       - Router.test_should_fail_on_withdraw_when_xtz_attached

    //       - Helper tests (proxy for ticket transfer)
    //       - Helper.test_should_allow_to_add_operator_to_fa2_token
    //       - Helper.test_should_allow_to_approve_and_reapprove_fa12_token

    def test_withdraw_router
        # Boris should have now L1 tickets too:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(boris),
        )
        self.assertEqual(balance, 5)

        # Boris unpacks some L1 tickets to get back some FA2 tokens
        boris_tokens_before_burn = fa2.get_balance(pkh(boris))

        boris.bulk(
            release_proxy.using(boris).set({
                'receiver': f'{ticketer.address}%withdraw',
                'data': pkh(boris),
            }),
            boris.transfer_ticket(
                ticket_contents=ticket['content'],
                ticket_ty=ticket['content_type'],
                ticket_ticketer=ticket['ticketer'],
                ticket_amount=2,
                destination=release_proxy.address,
                entrypoint='send',
            )
        ).send()
        self.bake_block()

        # Boris should have burned some L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(boris),
        )
        self.assertEqual(balance, 3)

    '''

    # TODO: test_should_be_able_to_unwrap_token_from_tickiter_with_helper
    #       - this is part of the first integration test which is commented
    #         above but it needs to use ticket helper instead of proxy
    # TODO: test_should_be_able_to_get_ticket_from_rollup_with_router
    #       - this is Ticketer test that probably described above
    # TODO: test_should_be_able_to_get_tokens_from_rollup_with_ticketer
    #       - this is part of the first integration test
    def test_should_be_able_to_deposit_with_ticket_helper(self) -> None:
        # TODO: consider split it to two tests: deposit and withdraw
        alice = self.accs['alice']
        fa2 = self.contracts['fa2']
        rollup_mock = self.contracts['rollup_mock']
        ticketer = self.contracts['ticketer']
        router = self.contracts['router']
        ticket_helper = self.contracts['ticket_helper']

        ticket = ticketer.get_ticket()

        # There are two addresses on L2, the first one is ERC20 proxy contract,
        # which would receve L2 tickets and the second is the Alice L2 address,
        # which would receive L2 tokens minted by ERC20 proxy contract:
        token_proxy = bytes.fromhex('0101010101010101010101010101010101010101')
        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')

        # In order to deposit token to the rollup, in one bulk operation:
        # - ticketer allowed to transfer tokens from Alice,
        # - Alice calls deposit tokens to the ticketer,
        # - Alice set routing info to the proxy
        #   (as far as implicit address can't send tickets with extra data),
        # - Alice transfer ticket to the Rollup via proxy contract.
        routing_data = token_proxy + alice_l2_address
        alice.bulk(
            fa2.using(alice).allow(ticket_helper.address),
            ticket_helper.using(alice).deposit(routing_data, 100),
        ).send()
        self.bake_block()

        # Checking deposit operations results:
        # - Rollup has L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            rollup_mock.address,
        )
        self.assertEqual(balance, 100)

        # - Ticketer has FA2 tokens:
        assert fa2.get_balance(ticketer.address) == 100

        # - Alice has no L1 tickets:
        balance = get_ticket_balance(
            self.client,
            ticket,
            pkh(alice),
        )
        self.assertEqual(balance, 0)
