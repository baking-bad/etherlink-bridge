from tests.base import BaseTestCase
from tests.helpers.utility import pkh, pack
from tests.helpers.tickets import create_ticket
from tests.helpers.contracts.proxy import ReleaseParams


class ProxyTestCase(BaseTestCase):
    def test_should_add_context_to_proxy_after_set(self) -> None:
        alice = self.accs['alice']
        release_proxy = self.contracts['release_proxy']
        ticketer = self.contracts['ticketer']

        # Checking that context is empty:
        init_context = release_proxy.get_context(pkh(alice))
        self.assertEqual(init_context, None)

        # Setting context to the proxy:
        expected_context: ReleaseParams = {
            'data': pkh(alice),
            'receiver': f'{ticketer.address}%release',
        }
        release_proxy.using(alice).set(expected_context).send()
        self.bake_block()

        # Checking that context is set:
        actual_context = release_proxy.get_context(pkh(alice))
        assert actual_context
        self.assertDictEqual(expected_context, actual_context)


    def test_should_clear_context_from_proxy_after_release(self) -> None:
        boris = self.accs['boris']
        alice = self.accs['alice']
        ticketer = self.contracts['ticketer']
        fa2 = self.contracts['fa2']
        release_proxy = self.contracts['release_proxy']

        # Preparing ticket for testing:
        boris.bulk(
            fa2.using(boris).allow(ticketer.address),
            ticketer.using(boris).deposit({'token': fa2, 'amount': 42}),
        ).send()
        self.bake_block()

        # Setting context to the proxy to unpack ticket and calling release:
        expected_context: ReleaseParams = {
            'data': pkh(boris),
            'receiver': f'{ticketer.address}%withdraw',
        }
        ticket = create_ticket(ticketer, fa2)
        boris.bulk(
            release_proxy.using(boris).set(expected_context),
            boris.transfer_ticket(
                ticket_contents=ticket['content'],
                ticket_ty=ticket['content_type'],
                ticket_ticketer=ticket['ticketer'],
                ticket_amount=42,
                destination=release_proxy.address,
                entrypoint='send',
            ),
        ).send()
        self.bake_block()

        # Checking that context is empty:
        actual_context = release_proxy.get_context(pkh(alice))
        self.assertEqual(actual_context, None)
