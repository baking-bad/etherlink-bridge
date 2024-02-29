from tezos.tests.base import BaseTestCase
from pytezos.rpc.errors import MichelsonError
from typing import Any
from tezos.tests.helpers.ticket_content import TicketContent
from tezos.tests.helpers.ticket import get_ticket_balance
from pytezos.client import PyTezosClient
from tezos.tests.helpers.contracts import (
    TicketHelper,
    RollupMock,
    TicketRouterTester,
)
from tezos.tests.helpers.ticket import Ticket


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
    def default_setup_helper(
        self,
        *args: Any,
        **kwargs: Any
    ) -> tuple[PyTezosClient, TicketHelper, RollupMock]:
        """Default setup for TicketHelper contract with given token and ticketer"""
        alice, token, ticketer, _ = self.default_setup(*args, **kwargs)
        helper = self.deploy_ticket_helper(token, ticketer, ERC20_PROXY)
        rollup_mock = self.deploy_rollup_mock()
        token.using(alice).allow(alice, helper).send()
        self.bake_block()

        return alice, helper, rollup_mock

    def setup_helper_bind_to_tester(
        self,
        *args: Any,
        **kwargs: Any
    ) -> tuple[PyTezosClient, TicketHelper, RollupMock, TicketRouterTester]:
        """Special setup with TicketRouterTester as a Ticketer which implements
        Ticketer.deposit interface and can be used to test TicketHelper context
        updates during deposit operations"""
        alice, token, _, tester = self.default_setup(*args, **kwargs)
        helper = self.deploy_ticket_helper(token, tester, ERC20_PROXY)  # type: ignore
        rollup_mock = self.deploy_rollup_mock()
        token.using(alice).allow(alice, helper).send()
        self.bake_block()

        return alice, helper, rollup_mock, tester

    def test_should_prepare_correct_routing_info(self) -> None:
        alice, helper, rollup_mock = self.default_setup_helper('FA2')

        rollup = f'{rollup_mock.address}%rollup'
        opg = helper.using(alice).deposit(rollup, RECEIVER, 99).send()
        self.bake_block()

        result = self.find_call_result(opg)
        assert len(result.operations) == 4  # type: ignore

        rollup_call = result.operations[3]  # type: ignore
        assert rollup_call['destination'] == rollup_mock.address
        assert select_routing_info(rollup_call) == RECEIVER + ERC20_PROXY

    def test_should_fail_if_routing_info_has_inccorrect_size(self) -> None:
        alice, helper, rollup_mock = self.default_setup_helper('FA2')

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
        alice, helper, rollup_mock = self.default_setup_helper('FA2')
        rollup = f'{rollup_mock.address}%rollup'
        helper.using(alice).deposit(rollup, RECEIVER, 15).send()
        self.bake_block()

        ticket = helper.get_ticketer().read_ticket(rollup_mock)
        assert ticket.amount == 15

    def test_deposit_succeed_for_correct_fa12_token_and_ticketer(self) -> None:
        alice, helper, rollup_mock = self.default_setup_helper('FA1.2')
        rollup = f'{rollup_mock.address}%rollup'
        helper.using(alice).deposit(rollup, RECEIVER, 1).send()
        self.bake_block()

        ticket = helper.get_ticketer().read_ticket(rollup_mock)
        assert ticket.amount == 1

    def test_context_updated_during_deposit(self) -> None:
        # Special setup with TicketRouterTester as a ticketer:
        alice, helper, rollup_mock, tester = self.setup_helper_bind_to_tester('FA2')
        rollup = f'{rollup_mock.address}%rollup'
        helper.using(alice).deposit(rollup, RECEIVER, 1).send()
        self.bake_block()

        expected_context = {
            'receiver': RECEIVER,
            'rollup': rollup,
        }
        context = helper.contract.storage['context']()
        assert context == expected_context

        # Minting ticket to the TicketHelper.default entrypoint to finalize deposit:
        some_ticket_content = TicketContent(1, bytes.fromhex('00'))
        alice.bulk(
            tester.set_default(helper),
            tester.mint(some_ticket_content, 111),
        ).send()
        self.bake_block()

        # Check that context is cleared after minting:
        assert helper.contract.storage['context']() is None

        # Check that rollup_mock has received the ticket:
        ticket_balance = get_ticket_balance(
            alice,
            rollup_mock,
            tester.address,
            some_ticket_content
        )
        assert ticket_balance == 111

    def test_should_not_accept_ticket_when_context_empty(self) -> None:
        # Special setup with TicketRouterTester as a ticketer:
        alice, helper, rollup_mock, tester = self.setup_helper_bind_to_tester('FA2')
        some_ticket_content = TicketContent(0, None)

        with self.assertRaises(MichelsonError) as err:
            alice.bulk(
                tester.set_default(helper),
                tester.mint(some_ticket_content, 1),
            ).send()
        assert 'ROUTING_DATA_IS_NOT_SET' in str(err.exception)

    def test_should_not_accept_ticket_from_wrong_sender(self) -> None:
        # Special setup with TicketRouterTester as a ticketer:
        alice, helper, rollup_mock, tester = self.setup_helper_bind_to_tester('FA2')
        content = TicketContent(0, None)

        # Setting up TicketHelper contract:
        rollup = f'{rollup_mock.address}%rollup'
        helper.using(alice).deposit(rollup, RECEIVER, 1).send()
        self.bake_block()

        # First mint ticket to Alice:
        alice.bulk(
            tester.set_default(alice),
            tester.mint(content, 1),
        ).send()
        self.bake_block()

        ticket = Ticket.create(alice, alice, tester.address, content)
        assert ticket.amount == 1

        # Then Alice tries to finalize deposit and it should fail:
        with self.assertRaises(MichelsonError) as err:
            ticket.transfer(helper).send()
        assert 'UNEXPECTED_SENDER' in str(err.exception)

        # Then using tester to redirect ticket back to TicketHelper:
        alice.bulk(
            tester.set_default(helper),
            ticket.transfer(tester),
        ).send()
        self.bake_block()

    def test_should_fail_on_deposit_with_attached_xtz(self) -> None:
        alice, helper, rollup_mock = self.default_setup_helper('FA2')
        rollup = f'{rollup_mock.address}%rollup'
        with self.assertRaises(MichelsonError) as err:
            helper.using(alice).deposit(rollup, RECEIVER, 1).with_amount(100).send()
        assert 'XTZ_DEPOSIT_DISALLOWED' in str(err.exception)

    def test_should_fail_on_unwrap_with_attached_xtz(self) -> None:
        alice, helper, rollup_mock = self.default_setup_helper('FA2')
        tester = self.deploy_ticket_router_tester()

        # It is impossible to deposit ticket with amount from implicit address,
        # so instead TicketRouterTester will be used to mint ticket to the helper.
        # To do this, first, mint ticket to Alice:
        ticketer = helper.get_ticketer()
        ticketer.using(alice).deposit(12).send()
        self.bake_block()

        ticket = ticketer.read_ticket(alice)
        assert ticket.amount == 12

        with self.assertRaises(MichelsonError) as err:
            alice.bulk(
                tester.set_default(
                    target=f'{helper.address}%unwrap',
                    xtz_amount=100,
                ),
                ticket.transfer(tester),
            ).send()
        assert 'XTZ_DEPOSIT_DISALLOWED' in str(err.exception)

        # Checking that transaction without XTZ will succeed:
        alice.bulk(
            tester.set_default(f'{helper.address}%unwrap'),
            ticket.transfer(tester),
        ).send()
        self.bake_block()
