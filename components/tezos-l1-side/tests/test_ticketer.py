from tests.base import BaseTestCase
from tests.helpers.utility import pkh, pack
from tests.helpers.tickets import get_all_tickets


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
                'decimals': pack(0, 'nat'),
                'symbol': pack('', 'string'),
            },
            'map %token_info string bytes',
        )

        expected_payload = {
            'prim': 'Pair',
            'args': [
                {'int': '0'},
                {'prim': 'Some', 'args': [{'bytes': token_info_bytes}]},
            ],
        }
