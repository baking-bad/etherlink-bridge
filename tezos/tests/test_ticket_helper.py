from tezos.tests.base import BaseTestCase
from tezos.tests.helpers.utility import pkh, pack

def select_routing_info(operation: dict[str, any]) -> bytes:
    """Special helper to select routing_info parameter from
    Rollup entrypoint which has the following michelson type:
        (or
            (or
                (pair %deposit
                    (bytes %routing_info)
                    (ticket %ticket (pair nat (option bytes)))
                )
                (bytes %b)
            )
            (bytes %c)
        )
    """

    value = operation['parameters']['value']
    left_1 = value['args'][0]
    left_2 = left_1['args'][0]
    pair = left_2['args'][0]
    routing_info = pair['bytes']
    return bytes.fromhex(routing_info)


class TicketHelperTestCase(BaseTestCase):
    def test_should_prepare_correct_routing_info(self) -> None:
        alice = self.bootstrap_account()
        balances = {pkh(alice): 1000}
        token, ticketer, erc_proxy, helper = self.setup_fa2(balances)
        rollup_mock = self.deploy_rollup_mock()
        token.using(alice).allow(pkh(alice), helper.address).send()
        self.bake_block()

        rollup = f'{rollup_mock.address}%rollup'
        l2_address = bytes.fromhex('abcdabcdabcdabcdabcdabcdabcdabcdabcdabcd')
        opg = helper.using(alice).deposit(rollup, l2_address, 99).send()
        self.bake_block()

        result = self.find_call_result(opg)
        assert len(result.operations) == 4

        rollup_call = result.operations[3]
        assert rollup_call['destination'] == rollup_mock.address
        assert select_routing_info(rollup_call) == l2_address + erc_proxy
