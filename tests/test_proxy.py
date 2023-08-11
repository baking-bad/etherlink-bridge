from tests.base import BaseTestCase
from tests.helpers.utility import pkh, pack
from tests.helpers.tickets import create_ticket
from tests.helpers.contracts.proxy import TicketerSetParams


class ProxyTestCase(BaseTestCase):
    def test_should_add_context_to_proxy_after_set(self) -> None:
        # Checking that context is empty:
        init_context = self.proxy_ticketer.get_context(pkh(self.alice))
        self.assertEqual(init_context, None)

        # Setting context to the proxy:
        expected_context: TicketerSetParams = {
            'data': pkh(self.alice),
            'receiver': f'{self.ticketer.address}%release',
        }
        self.proxy_ticketer.using(self.alice).set(expected_context).send()
        self.bake_block()

        # Checking that context is set:
        actual_context = self.proxy_ticketer.get_context(pkh(self.alice))
        assert actual_context
        self.assertDictEqual(expected_context, actual_context)


    def test_should_clear_context_from_proxy_after_release(self) -> None:
        # Preparing ticket for testing:
        self.boris.bulk(
            self.fa2.using(self.boris).allow(self.ticketer.address),
            self.ticketer.using(self.boris).deposit(self.fa2, 42),
        ).send()
        self.bake_block()

        # Setting context to the proxy to unpack ticket and calling release:
        expected_context: TicketerSetParams = {
            'data': pkh(self.boris),
            'receiver': f'{self.ticketer.address}%release',
        }
        ticket = create_ticket(
            ticketer=self.ticketer.address,
            token_id=0,
            token_info={
                'contract_address': pack(self.fa2.address, 'address'),
                'token_id': pack(self.fa2.token_id, 'nat'),
                'token_type': pack("FA2", 'string'),
                'decimals': pack(12, 'nat'),
                'symbol': pack('TEST', 'string'),
            },
        )
        self.boris.bulk(
            self.proxy_ticketer.using(self.boris).set(expected_context),
            self.boris.transfer_ticket(
                ticket_contents=ticket['content'],
                ticket_ty=ticket['content_type'],
                ticket_ticketer=ticket['ticketer'],
                ticket_amount=42,
                destination=self.proxy_ticketer.address,
                entrypoint='send',
            ),
        ).send()
        self.bake_block()

        # Checking that context is empty:
        actual_context = self.proxy_ticketer.get_context(pkh(self.alice))
        self.assertEqual(actual_context, None)
