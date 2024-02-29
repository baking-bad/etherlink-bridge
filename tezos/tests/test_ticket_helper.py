from tezos.tests.base import BaseTestCase
from pytezos.rpc.errors import MichelsonError
from typing import Any


def select_routing_info(operation: dict[str, Any]) -> bytes:
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


ERC20_PROXY = bytes.fromhex('fa00fa00fa00fa00fa00fa00fa00fa00fa00fa00')
RECEIVER = bytes.fromhex('abcdabcdabcdabcdabcdabcdabcdabcdabcdabcd')


class TicketHelperTestCase(BaseTestCase):
    def default_setup_helper(self, *args, **kwargs) -> tuple:  # type: ignore
        alice, token, ticketer, tester = self.default_setup(*args, **kwargs)
        helper = self.deploy_ticket_helper(token, ticketer, ERC20_PROXY)
        rollup_mock = self.deploy_rollup_mock()
        token.using(alice).allow(alice, helper).send()
        self.bake_block()

        return alice, helper, rollup_mock, tester

    def test_should_prepare_correct_routing_info(self) -> None:
        alice, helper, rollup_mock, _ = self.default_setup_helper('FA2')

        rollup = f'{rollup_mock.address}%rollup'
        opg = helper.using(alice).deposit(rollup, RECEIVER, 99).send()
        self.bake_block()

        result = self.find_call_result(opg)
        assert len(result.operations) == 4  # type: ignore

        rollup_call = result.operations[3]  # type: ignore
        assert rollup_call['destination'] == rollup_mock.address
        assert select_routing_info(rollup_call) == RECEIVER + ERC20_PROXY

    def test_should_fail_if_routing_info_has_inccorrect_size(self) -> None:
        alice, helper, rollup_mock, _ = self.default_setup_helper('FA2')

        rollup = f'{rollup_mock.address}%rollup'
        short_l2 = bytes.fromhex('abcdabcd')
        with self.assertRaises(MichelsonError) as err:
            helper.using(alice).deposit(rollup, short_l2, 33).send()
        assert 'WRONG_ROUTING_INFO_LENGTH' in str(err.exception)

        long_l2 = bytes.fromhex('abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd')
        with self.assertRaises(MichelsonError) as err:
            helper.using(alice).deposit(rollup, long_l2, 33).send()
        assert 'WRONG_ROUTING_INFO_LENGTH' in str(err.exception)

    def test_deposit_succeed_for_correct_fa2_token_and_ticketer(self) -> None:
        alice, helper, rollup_mock, _ = self.default_setup_helper('FA2')
        rollup = f'{rollup_mock.address}%rollup'
        helper.using(alice).deposit(rollup, RECEIVER, 15).send()
        self.bake_block()

        ticket = helper.get_ticketer().read_ticket(rollup_mock)
        assert ticket.amount == 15
