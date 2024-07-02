from tezos.tests.base import BaseTestCase
from pytezos.rpc.errors import MichelsonError
from scripts.helpers.utility import pack
from scripts.helpers.ticket_content import TicketContent


class TicketerTestCase(BaseTestCase):
    def test_create_ticket_on_deposit_fa12_if_token_expected(self) -> None:
        alice, token, ticketer, _ = self.default_setup('FA1.2')

        # Alice deposits 42 tokens to the Ticketer and creates a ticket:
        ticketer.using(alice).deposit(42).send()
        self.bake_block()
        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 42
        assert token.get_balance(ticketer) == 42

        # Alice deposit 1 more token to the Ticketer and ticket stacked:
        ticketer.using(alice).deposit(1).send()
        self.bake_block()
        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 43
        assert token.get_balance(ticketer) == 43

        # Checking ticket payload:
        token_info_bytes = pack(
            {
                'contract_address': token.address.encode(),
                'token_type': "FA1.2".encode(),
            },
            'map %token_info string bytes',
        ).hex()

        expected_payload = {
            'prim': 'Pair',
            'args': [
                {'int': '0'},
                {'prim': 'Some', 'args': [{'bytes': token_info_bytes}]},
            ],
        }
        self.assertDictEqual(ticket.content.to_micheline(), expected_payload)

    def test_create_ticket_on_deposit_fa2_if_token_expected(self) -> None:
        alice, token, ticketer, _ = self.default_setup(
            token_type='FA2',
            extra_metadata={
                'decimals': '12',
                'symbol': 'FA2',
            },
        )

        # Alice deposits 1 token to the Ticketer and creates a ticket:
        ticketer.using(alice).deposit(1).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 1
        assert token.get_balance(ticketer) == 1

        # Checking ticket payload:
        token_info_bytes = pack(
            {
                'contract_address': token.address.encode(),
                'token_type': 'FA2'.encode(),
                'token_id': '0'.encode(),
                'decimals': '12'.encode(),
                'symbol': 'FA2'.encode(),
            },
            'map %token_info string bytes',
        ).hex()

        expected_payload = {
            'prim': 'Pair',
            'args': [
                {'int': '0'},
                {'prim': 'Some', 'args': [{'bytes': token_info_bytes}]},
            ],
        }
        self.assertDictEqual(ticket.content.to_micheline(), expected_payload)

    def test_should_send_fa2_to_receiver_on_withdraw_if_ticket_correct(self) -> None:
        alice, token, ticketer, _ = self.default_setup('FA2', balance=100)

        # Alice deposits 100 FA2 tokens to the Ticketer without using helper contract:
        ticketer.using(alice).deposit(100).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 100
        assert token.get_balance(ticketer) == 100
        assert token.get_balance(alice) == 0

        # Alice uses helper contract to unwrap 42 tickets back to tokens:
        helper = self.deploy_token_bridge_helper(token, ticketer)
        spent_ticket, kept_ticket = ticket.split(42)
        spent_ticket.transfer(helper, 'unwrap').send()
        self.bake_block()

        assert kept_ticket.amount == 100 - 42
        assert token.get_balance(ticketer) == 100 - 42
        assert token.get_balance(alice) == 42

    def test_should_send_fa12_to_receiver_on_withdraw_if_ticket_correct(self) -> None:
        alice, token, ticketer, _ = self.default_setup('FA1.2', balance=1)

        # Alice deposits 1 FA1.2 token to the Ticketer without using helper contract:
        ticketer.using(alice).deposit(1).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 1
        assert token.get_balance(ticketer) == 1
        assert token.get_balance(alice) == 0

        # Alice uses helper contract to unwrap tickets back to tokens:
        helper = self.deploy_token_bridge_helper(token, ticketer)
        ticket.transfer(helper, 'unwrap').send()
        self.bake_block()

        assert ticketer.read_ticket(alice).amount == 0
        assert token.get_balance(ticketer) == 0
        assert token.get_balance(alice) == 1

    def test_should_not_allow_to_mint_new_ticket_if_total_supply_exceeds_max(
        self,
    ) -> None:
        alice, token, ticketer, _ = self.default_setup('FA1.2', balance=2**256)

        # Alice not able to deposit 2**256 tokens to the Ticketer:
        with self.assertRaises(MichelsonError) as err:
            ticketer.using(alice).deposit(2**256).send()
        assert 'TOTAL_SUPPLY_EXCEED_MAX' in str(err.exception)

        # But Alice able to deposit 2**256-1 tokens to the Ticketer:
        ticketer.using(alice).deposit(2**256 - 1).send()
        self.bake_block()

        assert ticketer.read_ticket(alice).amount == 2**256 - 1
        assert token.get_balance(ticketer) == 2**256 - 1

        # Alice tries to deposit 1 more token and it fails:
        with self.assertRaises(MichelsonError) as err:
            ticketer.using(alice).deposit(1).send()
        assert 'TOTAL_SUPPLY_EXCEED_MAX' in str(err.exception)

    def test_should_fail_to_unpack_ticket_minted_by_another_ticketer(self) -> None:
        alice, token, ticketer, tester = self.default_setup('FA2')

        # Alice locks 100 tokens on the Ticketer and creates a ticket:
        ticketer.using(alice).deposit(100).send()
        self.bake_block()

        # Making sure that ticketer has 100 FA2 tokens:
        assert token.get_balance(ticketer) == 100

        # Minting fake ticket and sending it to the ticketer fails:
        ticket = ticketer.read_ticket(alice)
        boris = self.bootstrap_account()
        with self.assertRaises(MichelsonError) as err:
            boris.bulk(
                tester.set_router_withdraw(
                    target=ticketer,
                    receiver=boris,
                ),
                tester.mint(ticket.content, 100),
            ).send()
        assert 'UNAUTHORIZED_TKTR' in str(err.exception)

    def test_should_fail_to_unpack_ticket_with_incorrect_content(self) -> None:
        alice, token, ticketer, tester = self.default_setup('FA2')
        empty_content = TicketContent(
            token_id=0,
            token_info=None,
        )

        # Minting fake ticket and sending it to the ticketer with
        # incorrect content fails:
        with self.assertRaises(MichelsonError) as err:
            alice.bulk(
                tester.set_router_withdraw(
                    target=ticketer,
                    receiver=alice,
                ),
                tester.mint(empty_content, 1),
            ).send()

        # NOTE: it is important to check for the error message here
        # because along with wrong content, the ticketer address is also wrong.
        # Also the content check is done before the ticketer address check.
        assert 'UNEXPECTED_TKT_CONTENT' in str(err.exception)

    def test_should_fail_on_deposit_with_attached_xtz(self) -> None:
        alice, token, ticketer, _ = self.default_setup('FA2')

        # Alice fails to deposit 1 token to the Ticketer with attached 1 mutez:
        with self.assertRaises(MichelsonError) as err:
            ticketer.using(alice).deposit(1).with_amount(1).send()
        assert 'XTZ_DEPOSIT_DISALLOWED' in str(err.exception)

    def test_should_fail_on_withdraw_with_attached_xtz(self) -> None:
        alice, token, ticketer, tester = self.default_setup('FA1.2')

        ticketer.using(alice).deposit(1).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 1

        # Alice fails to withdraw 1 token from the Ticketer with attached 1 mutez:
        with self.assertRaises(MichelsonError) as err:
            alice.bulk(
                tester.set_router_withdraw(
                    target=ticketer,
                    receiver=alice,
                    xtz_amount=1,
                ).with_amount(1),
                ticket.transfer(tester),
            ).send()
        assert 'XTZ_DEPOSIT_DISALLOWED' in str(err.exception)

        # Alice succeeds to withdraw token in the same setup without xtz attached:
        alice.bulk(
            tester.set_router_withdraw(
                target=ticketer,
                receiver=alice,
            ),
            ticket.transfer(tester),
        ).send()

    def test_should_increase_total_supply(self) -> None:
        alice, token, ticketer, tester = self.default_setup('FA1.2')

        # Alice deposits 10 tokens to the Ticketer:
        ticketer.using(alice).deposit(10).send()
        self.bake_block()
        assert ticketer.get_total_supply_view() == 10

        # Alice deposits 100 more tokens to the Ticketer:
        ticketer.using(alice).deposit(100).send()
        self.bake_block()
        assert ticketer.get_total_supply_view() == 110

    def test_should_decrease_total_supply(self) -> None:
        alice, token, ticketer, tester = self.default_setup('FA2')

        # Alice deposits 100 tokens to the Ticketer:
        ticketer.using(alice).deposit(100).send()
        self.bake_block()
        assert ticketer.get_total_supply_view() == 100

        # Alice withdraws 10 tokens from the Ticketer:
        ticket = ticketer.read_ticket(alice)
        spent_ticket, _ = ticket.split(10)
        alice.bulk(
            tester.set_router_withdraw(
                target=ticketer,
                receiver=alice,
            ),
            spent_ticket.transfer(tester),
        ).send()
        self.bake_block()
        assert ticketer.get_total_supply_view() == 100 - 10

    def test_create_ticket_on_deposit_fa2_with_non_zero_id(self) -> None:
        alice, token, ticketer, _ = self.default_setup('FA2', token_id=42)

        # Alice successfully deposits 1 token to the Ticketer:
        ticketer.using(alice).deposit(1).send()
        self.bake_block()

        # Alice has one ticket with 1 token:
        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 1
        assert token.get_balance(ticketer) == 1

    def test_should_return_content_on_view_call_for_fa12(self) -> None:
        alice, token, ticketer, _ = self.default_setup(
            token_type='FA1.2',
            extra_metadata={
                'decimals': '16',
                'symbol': 'tBTC',
            },
        )

        token_info_bytes = pack(
            {
                'contract_address': token.address.encode(),
                'token_type': 'FA1.2'.encode(),
                'decimals': '16'.encode(),
                'symbol': 'tBTC'.encode(),
            },
            'map %token_info string bytes',
        )
        expected_content = (0, token_info_bytes)

        actual_content = ticketer.get_content_view()
        assert actual_content == expected_content

    def test_should_return_content_on_view_call_for_fa2(self) -> None:
        alice, token, ticketer, _ = self.default_setup(
            token_type='FA2',
            token_id=42,
            extra_metadata={
                'symbol': 'NFT',
            },
        )

        token_info_bytes = pack(
            {
                'contract_address': token.address.encode(),
                'token_type': 'FA2'.encode(),
                'token_id': '42'.encode(),
                'symbol': 'NFT'.encode(),
            },
            'map %token_info string bytes',
        )

        # NOTE: token_id for Ticketer content might be different from the
        # token_id of the wrapped token. It depends on Ticketer
        # implementation and on how it is configured during deployment.
        expected_content = (0, token_info_bytes)

        actual_content = ticketer.get_content_view()
        assert actual_content == expected_content

    def test_should_return_token_on_view_call_for_fa12(self) -> None:
        alice, token, ticketer, _ = self.default_setup('FA1.2')
        expected_token = {'fa12': token.address}
        actual_token = ticketer.get_token_view()

        assert actual_token == expected_token

    def test_should_return_token_on_view_call_for_fa2(self) -> None:
        alice, token, ticketer, _ = self.default_setup('FA2', token_id=777)
        expected_token = {'fa2': (token.address, 777)}
        actual_token = ticketer.get_token_view()

        assert actual_token == expected_token
