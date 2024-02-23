from tezos.tests.base import BaseTestCase
from pytezos.rpc.errors import MichelsonError
from tezos.tests.helpers.utility import pkh, pack


class TicketerTestCase(BaseTestCase):
    def test_create_ticket_on_deposit_fa12_if_token_expected(self) -> None:
        alice = self.bootstrap_account()
        token = self.deploy_fa12({pkh(alice): 100})
        ticketer = self.deploy_ticketer(token)
        ticket = ticketer.get_ticket()
        token.using(alice).allow(pkh(alice), ticketer.address).send()
        self.bake_block()

        # Alice deposits 42 tokens to the Ticketer and creates a ticket:
        ticketer.using(alice).deposit(42).send()
        self.bake_block()
        assert ticket.get_balance(pkh(alice)) == 42
        assert token.get_balance(ticketer.address) == 42

        # Alice deposit 1 more token to the Ticketer and ticket stacked:
        ticketer.using(alice).deposit(1).send()
        self.bake_block()
        assert ticket.get_balance(pkh(alice)) == 43
        assert token.get_balance(ticketer.address) == 43

        # Checking ticket payload:
        token_info_bytes = pack(
            {
                'contract_address': pack(token.address, 'address'),
                'token_type': pack("FA1.2", 'string'),
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
        self.assertDictEqual(ticket.content, expected_payload)

    def test_create_ticket_on_deposit_fa2_if_token_expected(self) -> None:
        alice = self.bootstrap_account()
        token = self.deploy_fa2({pkh(alice): 100})
        extra_metadata = {
            'decimals': pack(12, 'nat'),
            'symbol': pack('FA2', 'string'),
        }
        ticketer = self.deploy_ticketer(token, extra_metadata)
        ticket = ticketer.get_ticket()
        token.using(alice).allow(pkh(alice), ticketer.address).send()
        self.bake_block()

        # Alice deposits 1 token to the Ticketer and creates a ticket:
        ticketer.using(alice).deposit(1).send()
        self.bake_block()
        assert ticket.get_balance(pkh(alice)) == 1
        assert token.get_balance(ticketer.address) == 1

        # Checking ticket payload:
        token_info_bytes = pack(
            {
                'contract_address': pack(token.address, 'address'),
                'token_type': pack('FA2', 'string'),
                'token_id': pack(0, 'nat'),
                'decimals': pack(12, 'nat'),
                'symbol': pack('FA2', 'string'),
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
        self.assertDictEqual(ticket.content, expected_payload)

    def test_should_send_fa2_to_receiver_on_withdraw_if_ticket_correct(self) -> None:
        alice = self.bootstrap_account()
        balances = {pkh(alice): 100}
        token, ticketer, _, helper = self.setup_fa2(balances)
        ticket = ticketer.get_ticket()

        # Alice deposits 100 FA2 tokens to the Ticketer without using helper contract:
        alice.bulk(
            token.allow(pkh(alice), ticketer.address),
            ticketer.deposit(100),
        ).send()
        self.bake_block()

        assert ticket.get_balance(pkh(alice)) == 100
        assert token.get_balance(ticketer.address) == 100
        assert token.get_balance(pkh(alice)) == 0

        # Alice uses helper contract to unwrap tickets back to tokens:
        entrypoint = f'{helper.address}%unwrap'
        ticket.using(alice).transfer(entrypoint, 42).send()
        self.bake_block()

        assert ticket.get_balance(pkh(alice)) == 100 - 42
        assert token.get_balance(ticketer.address) == 100 - 42
        assert token.get_balance(pkh(alice)) == 42

    def test_should_send_fa12_to_receiver_on_withdraw_if_ticket_correct(self) -> None:
        alice = self.bootstrap_account()
        balances = {pkh(alice): 1}
        token, ticketer, _, helper = self.setup_fa12(balances)
        ticket = ticketer.get_ticket()

        # Alice deposits 1 FA1.2 token to the Ticketer without using helper contract:
        alice.bulk(
            token.allow(pkh(alice), ticketer.address),
            ticketer.deposit(1),
        ).send()
        self.bake_block()

        assert ticket.get_balance(pkh(alice)) == 1
        assert token.get_balance(ticketer.address) == 1
        assert token.get_balance(pkh(alice), allow_key_error=True) == 0

        # Alice uses helper contract to unwrap tickets back to tokens:
        entrypoint = f'{helper.address}%unwrap'
        ticket.using(alice).transfer(entrypoint, 1).send()
        self.bake_block()

        assert ticket.get_balance(pkh(alice)) == 0
        assert token.get_balance(ticketer.address, allow_key_error=True) == 0
        assert token.get_balance(pkh(alice)) == 1

    def test_should_not_allow_to_mint_new_ticket_if_total_supply_exceeds_max(
        self,
    ) -> None:
        alice = self.bootstrap_account()
        balances = {pkh(alice): 2**256}
        token, ticketer, _, helper = self.setup_fa2(balances)
        ticket = ticketer.get_ticket()
        token.using(alice).allow(pkh(alice), ticketer.address).send()
        self.bake_block()

        # Alice not able to deposit 2**256 tokens to the Ticketer:
        with self.assertRaises(MichelsonError) as err:
            ticketer.using(alice).deposit(2**256).send()
        assert 'TOTAL_SUPPLY_EXCEED_MAX' in str(err.exception)

        # But Alice able to deposit 2**256-1 tokens to the Ticketer:
        ticketer.using(alice).deposit(2**256 - 1).send()
        self.bake_block()

        assert ticket.get_balance(pkh(alice)) == 2**256 - 1
        assert token.get_balance(ticketer.address) == 2**256 - 1

        # Alice tries to deposit 1 more token and it fails:
        with self.assertRaises(MichelsonError) as err:
            ticketer.using(alice).deposit(1).send()
        assert 'TOTAL_SUPPLY_EXCEED_MAX' in str(err.exception)
