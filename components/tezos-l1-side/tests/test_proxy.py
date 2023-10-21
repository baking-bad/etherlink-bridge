from tests.base import BaseTestCase
from tests.helpers.utility import pkh, pack
from tests.helpers.tickets import create_ticket
from tests.helpers.contracts.proxy import TicketerSetParams


class ProxyTestCase(BaseTestCase):
    def test_should_add_context_to_proxy_after_set(self) -> None:
        alice = self.accs['alice']
        proxy_ticketer = self.contracts['proxy_ticketer']
        ticketer = self.contracts['ticketer']

        # Checking that context is empty:
        init_context = proxy_ticketer.get_context(pkh(alice))
        self.assertEqual(init_context, None)

        # Setting context to the proxy:
        expected_context: TicketerSetParams = {
            'data': pkh(alice),
            'receiver': f'{ticketer.address}%release',
        }
        proxy_ticketer.using(alice).set(expected_context).send()
        self.bake_block()

        # Checking that context is set:
        actual_context = proxy_ticketer.get_context(pkh(alice))
        assert actual_context
        self.assertDictEqual(expected_context, actual_context)


    def test_should_clear_context_from_proxy_after_release(self) -> None:
        boris = self.accs['boris']
        alice = self.accs['alice']
        ticketer = self.contracts['ticketer']
        fa2 = self.contracts['fa2']
        proxy_ticketer = self.contracts['proxy_ticketer']

        # Preparing ticket for testing:
        boris.bulk(
            fa2.using(boris).allow(ticketer.address),
            ticketer.using(boris).deposit(fa2, 42),
        ).send()
        self.bake_block()

        # Setting context to the proxy to unpack ticket and calling release:
        expected_context: TicketerSetParams = {
            'data': pkh(boris),
            'receiver': f'{ticketer.address}%release',
        }
        ticket = create_ticket(
            ticketer=ticketer.address,
            token_id=0,
            token_info={
                'contract_address': pack(fa2.address, 'address'),
                'token_id': pack(fa2.token_id, 'nat'),
                'token_type': pack("FA2", 'string'),
                'decimals': pack(12, 'nat'),
                'symbol': pack('TEST', 'string'),
            },
        )
        boris.bulk(
            proxy_ticketer.using(boris).set(expected_context),
            boris.transfer_ticket(
                ticket_contents=ticket['content'],
                ticket_ty=ticket['content_type'],
                ticket_ticketer=ticket['ticketer'],
                ticket_amount=42,
                destination=proxy_ticketer.address,
                entrypoint='send',
            ),
        ).send()
        self.bake_block()

        # Checking that context is empty:
        actual_context = proxy_ticketer.get_context(pkh(alice))
        self.assertEqual(actual_context, None)
