from tezos.tests.base import BaseTestCase


class TicketerRouterTesterTestCase(BaseTestCase):
    def test_should_allow_to_deposit_to_the_rollup_without_erc_proxy(self) -> None:
        alice, token, ticketer, tester = self.default_setup('FA2')
        rollup_mock = self.deploy_rollup_mock()

        alice_l2_address = bytes.fromhex('0202020202020202020202020202020202020202')
        alice.bulk(
            token.allow(alice, ticketer),
            ticketer.deposit(100),
        ).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 100

        alice.bulk(
            tester.set_rollup_deposit(
                target=f'{rollup_mock.address}%rollup',
                routing_info=alice_l2_address,
            ),
            ticket.transfer(tester),
        ).send()
        self.bake_block()
        assert ticketer.read_ticket(rollup_mock).amount == 100
