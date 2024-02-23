from tezos.tests.base import BaseTestCase
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
        ticketer.using(alice).deposit({'amount': 42}).send()
        self.bake_block()
        assert ticket.get_balance(pkh(alice)) == 42
        assert token.get_balance(ticketer.address) == 42

        # Alice deposit 1 more token to the Ticketer and ticket stacked:
        ticketer.using(alice).deposit({'amount': 1}).send()
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
        ticketer.using(alice).deposit({'amount': 1}).send()
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
        token = self.deploy_fa2({pkh(alice): 100})
        ticketer = self.deploy_ticketer(token)
        ticket = ticketer.get_ticket()
        erc_proxy = bytes.fromhex('0101010101010101010101010101010101010101')
        helper = self.deploy_ticket_helper(token, ticketer, erc_proxy)

        # Alice deposits 100 FA2 tokens to the Ticketer without using helper contract:
        alice.bulk(
            token.allow(pkh(alice), ticketer.address),
            ticketer.deposit({'amount': 100}),
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
        token = self.deploy_fa12({pkh(alice): 1})
        ticketer = self.deploy_ticketer(token)
        ticket = ticketer.get_ticket()
        erc_proxy = bytes.fromhex('0101010101010101010101010101010101010101')
        helper = self.deploy_ticket_helper(token, ticketer, erc_proxy)

        # Alice deposits 1 FA1.2 token to the Ticketer without using helper contract:
        alice.bulk(
            token.allow(pkh(alice), ticketer.address),
            ticketer.deposit({'amount': 1}),
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
