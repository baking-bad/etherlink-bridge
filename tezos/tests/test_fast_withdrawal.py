from dataclasses import dataclass
from decimal import Decimal
from typing import cast
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from pytezos.rpc.errors import MichelsonError
from scripts.helpers.contracts.xtz_ticketer import XtzTicketer
from scripts.helpers.contracts.fast_withdrawal import FastWithdrawal, Withdrawal
from scripts.helpers.contracts.ticket_router_tester import TicketRouterTester
from scripts.helpers.contracts.tokens.token import TokenHelper
from scripts.helpers.ticket_content import TicketContent
from scripts.helpers.utility import pack
from tezos.tests.base import BaseTestCase
from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.utility import decode_event


@dataclass
class FastWithdrawalTestSetup:
    manager: PyTezosClient
    withdrawer: PyTezosClient
    smart_rollup: PyTezosClient
    service_provider: PyTezosClient
    xtz_ticketer: XtzTicketer
    fast_withdrawal: FastWithdrawal
    tester: TicketRouterTester
    valid_timestamp: int
    expired_timestamp: int
    future_timestamp: int


class FastWithdrawalTestCase(BaseTestCase):
    def deploy_fast_withdrawal(
        self,
        xtz_ticketer: Addressable,
        smart_rollup: Addressable,
        expiration_seconds: int,
    ) -> FastWithdrawal:
        """Deploys FastWithdrawal contract for the specified xtz_ticketer and
        smart_rollup addresses"""

        opg = FastWithdrawal.originate(
            self.manager, xtz_ticketer, smart_rollup, expiration_seconds
        ).send()
        self.bake_block()
        return FastWithdrawal.from_opg(self.manager, opg)

    def deploy_xtz_ticketer(
        self,
    ) -> XtzTicketer:
        """Deploys XtzTicketer (exchanger) contract"""

        opg = XtzTicketer.originate(self.manager).send()
        self.bake_block()
        return XtzTicketer.from_opg(self.manager, opg)

    def bootstrap_non_baker_account(
        self, mutez_balance: int = 1_000_000_000
    ) -> PyTezosClient:
        key = self.manager.key.generate(export=False)
        account = self.manager.using(key=key)
        transaction = self.manager.transaction(
            destination=get_address(account), amount=mutez_balance
        )
        transaction = cast(OperationGroup, transaction)
        transaction.send()
        self.bake_block()

        cast(OperationGroup, account.reveal()).send()
        return account  # type: ignore

    def fast_withdrawal_setup(
        self,
    ) -> FastWithdrawalTestSetup:
        withdrawer = self.bootstrap_non_baker_account()
        service_provider = self.bootstrap_non_baker_account()
        smart_rollup = self.bootstrap_non_baker_account()
        self.bake_block()

        xtz_ticketer = self.deploy_xtz_ticketer()
        tester = self.deploy_ticket_router_tester()
        one_day = 24 * 60 * 60
        fast_withdrawal = self.deploy_fast_withdrawal(
            xtz_ticketer, tester, expiration_seconds=one_day
        )

        return FastWithdrawalTestSetup(
            manager=self.manager,
            withdrawer=withdrawer,
            service_provider=service_provider,
            smart_rollup=smart_rollup,
            xtz_ticketer=xtz_ticketer,
            fast_withdrawal=fast_withdrawal,
            tester=tester,
            valid_timestamp=self.manager.now(),
            expired_timestamp=self.manager.now() - one_day - 1,
            future_timestamp=self.manager.now() + one_day,
        )

    def test_should_create_withdrawal_record_after_xtz_withdrawal_purchased(
        self,
    ) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            payload=pack(1_000_000, 'nat'),
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            timestamp=setup.valid_timestamp,
        )
        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=setup.service_provider,
            xtz_amount=1_000_000,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

    def test_should_correctly_encode_payloads_for_different_ticket_amounts(
        self,
    ) -> None:
        setup = self.fast_withdrawal_setup()

        # NOTE: the manager account balance is 3.7 million xtz
        amounts = [1, 17, 1_000_000_000_000]

        for amount in amounts:
            withdrawal = Withdrawal.default_with(
                full_amount=amount,
                ticketer=setup.xtz_ticketer,
                content=TicketContent(0, None),
                base_withdrawer=setup.withdrawer,
                payload=pack(amount, 'nat'),
                timestamp=setup.valid_timestamp,
            )

            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
                xtz_amount=amount,
            ).send()
            self.bake_block()

            status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
            assert status.get_service_provider() == get_address(setup.service_provider)

    def test_should_create_different_withdrawal_records(self) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal(
            withdrawal_id=1000,
            full_amount=1_000_000,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            base_withdrawer=setup.withdrawer,
            timestamp=setup.valid_timestamp,
            payload=pack(999_500, 'nat'),
            l2_caller=bytes(20),
        )

        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=setup.service_provider,
            xtz_amount=999_500,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

        # Changing timestamp:
        withdrawal.timestamp = setup.valid_timestamp + 1
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=setup.service_provider,
            withdrawal=withdrawal,
            xtz_amount=999_500,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

        # Changing base_withdrawer:
        withdrawal.base_withdrawer = self.bootstrap_account()
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=setup.service_provider,
            withdrawal=withdrawal,
            xtz_amount=999_500,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

        # Changing payload:
        withdrawal.payload = pack(777_000, 'nat')
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=setup.service_provider,
            withdrawal=withdrawal,
            xtz_amount=777_000,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

        # Changing l2_caller:
        withdrawal.l2_caller = bytes.fromhex('ab' * 20)
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=setup.service_provider,
            withdrawal=withdrawal,
            xtz_amount=777_000,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

        # Changing ticketer and content:
        token = self.deploy_fa12(balances={setup.service_provider: 1_000_000})
        ticketer = self.deploy_ticketer(token, {})
        withdrawal.ticketer = ticketer
        withdrawal.content = ticketer.read_content()

        setup.service_provider.bulk(
            token.allow(setup.service_provider, setup.fast_withdrawal),
            setup.fast_withdrawal.payout_withdrawal(
                service_provider=setup.service_provider,
                withdrawal=withdrawal,
            ),
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

    def test_should_reject_duplicate_withdrawal(self) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            payload=pack(1_000_000, 'nat'),
            timestamp=setup.valid_timestamp,
        )
        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=setup.service_provider,
            xtz_amount=1_000_000,
        ).send()
        self.bake_block()

        # Checking that the same withdrawal can't be paid again by another provider:
        another_provider = self.bootstrap_account()
        with self.assertRaises(MichelsonError) as err:
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=another_provider,
                xtz_amount=1_000_000,
            ).send()
        assert "The fast withdrawal was already payed" in str(err.exception)

        # Checking that the same withdrawal can't be paid again by the same provider:
        with self.assertRaises(MichelsonError) as err:
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
                xtz_amount=1_000_000,
            ).send()
        assert "The fast withdrawal was already payed" in str(err.exception)

        # Check that the same withdrawal can't be paid again after it was finalized
        setup.xtz_ticketer.mint(setup.smart_rollup, 1_000_000).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.smart_rollup)

        setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        with self.assertRaises(MichelsonError) as err:
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=another_provider,
                xtz_amount=1_000_000,
            ).send()
        assert "The fast withdrawal was already payed" in str(err.exception)

    def test_provider_receives_xtz_withdrawal_after_purchase(self) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            full_amount=77,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            payload=pack(77, 'nat'),
            timestamp=setup.valid_timestamp,
        )
        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=setup.service_provider,
            xtz_amount=77,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

        # Creating wrapped xtz ticket for Smart Rollup:
        setup.xtz_ticketer.mint(setup.smart_rollup, 77).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.smart_rollup)

        # Recording providers balance:
        provider_balance = setup.service_provider.balance()

        # Settle withdrawal: (sending ticket to the fast withdrawal
        # contract `default` entrypoint):
        setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Checking that status is now Finished:
        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.is_finished()

        # Checking that the provider received the xtz:
        updated_balance = setup.service_provider.balance()
        assert updated_balance == provider_balance + Decimal('0.000077')

    def test_user_receives_xtz_withdrawal_when_no_purchase_made(self) -> None:
        setup = self.fast_withdrawal_setup()
        withdrawer_balance = setup.withdrawer.balance()

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            timestamp=setup.valid_timestamp,
        )
        self.bake_block()

        # Creating wrapped xtz ticket:
        setup.xtz_ticketer.mint(setup.service_provider, 333).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.service_provider)

        # No one purchased the withdrawal,
        # Sending ticket to the fast withdrawal contract `default` entrypoint:
        setup.service_provider.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Checking that withdrawer received the xtz (full withdrawal amount):
        assert setup.withdrawer.balance() == withdrawer_balance + Decimal('0.000333')

    def test_provider_receives_fa2_withdrawal_after_purchase(self) -> None:
        setup = self.fast_withdrawal_setup()

        token: TokenHelper = self.deploy_fa2(
            balances={setup.service_provider: 1_000, setup.smart_rollup: 1_000},
            token_id=33,
        )
        ticketer = self.deploy_ticketer(token, {})

        withdrawal = Withdrawal.default_with(
            full_amount=50,
            ticketer=ticketer,
            content=ticketer.read_content(),
            base_withdrawer=setup.withdrawer,
            payload=pack(30, 'nat'),
            timestamp=setup.valid_timestamp,
        )
        setup.service_provider.bulk(
            token.allow(setup.service_provider, setup.fast_withdrawal),
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
            ),
        ).send()
        self.bake_block()
        assert token.get_balance(setup.service_provider) == 1000 - 30
        assert token.get_balance(setup.withdrawer) == 30

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)

        # Creating wrapped token (ticket) for smart_rollup:
        setup.smart_rollup.bulk(
            token.allow(setup.smart_rollup, ticketer),
            ticketer.deposit(50),
        ).send()
        self.bake_block()
        ticket = ticketer.read_ticket(setup.smart_rollup)
        assert token.get_balance(setup.smart_rollup) == 1000 - 50

        # Settle withdrawal: (sending ticket to the fast withdrawal
        # contract `default` entrypoint):
        setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Checking that status is now Finished:
        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.is_finished()

        # Checking that the provider received the token:
        assert token.get_balance(setup.service_provider) == 1000 - 30 + 50

    def test_user_receives_fa12_withdrawal_when_no_purchase_made(self) -> None:
        setup = self.fast_withdrawal_setup()

        token: TokenHelper = self.deploy_fa12(
            balances={setup.smart_rollup: 100},
        )
        ticketer = self.deploy_ticketer(token, {})

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            ticketer=ticketer,
            content=TicketContent(0, None),
            timestamp=setup.valid_timestamp,
        )
        self.bake_block()

        # Creating wrapped token (ticket) for smart_rollup:
        setup.smart_rollup.bulk(
            token.allow(setup.smart_rollup, ticketer),
            ticketer.deposit(3),
        ).send()
        self.bake_block()
        ticket = ticketer.read_ticket(setup.smart_rollup)
        assert token.get_balance(setup.smart_rollup) == 100 - 3

        # No one purchased the withdrawal,
        # Sending ticket to the fast withdrawal contract `default` entrypoint:
        setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Checking that withdrawer received the token (full withdrawal amount):
        assert token.get_balance(setup.withdrawer) == 3

    def test_should_allow_xtz_withdrawal_purchase_at_full_price_after_timestamp_expired(
        self,
    ) -> None:
        setup = self.fast_withdrawal_setup()
        withdrawer_balance = setup.withdrawer.balance()

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            full_amount=1_000,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            payload=pack(990, 'nat'),
            timestamp=setup.expired_timestamp,
        )
        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=setup.service_provider,
            xtz_amount=1_000,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(setup.service_provider)
        assert setup.withdrawer.balance() == withdrawer_balance + Decimal('0.001000')

        # Creating wrapped xtz ticket for Smart Rollup:
        setup.xtz_ticketer.mint(setup.smart_rollup, 1000).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.smart_rollup)

        provider_balance = setup.service_provider.balance()
        setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        updated_balance = setup.service_provider.balance()
        assert updated_balance == provider_balance + Decimal('0.001000')

    def test_rejects_xtz_withdrawal_purchase_at_discounted_price_if_expired(
        self,
    ) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            full_amount=1_000,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            payload=pack(990, 'nat'),
            timestamp=setup.expired_timestamp,
        )
        with self.assertRaises(MichelsonError) as err:
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
                xtz_amount=990,
            ).send()
        assert "Tezos amount is not valid" in str(err.exception)

    def test_should_reject_xtz_withdrawal_purchase_with_wrong_xtz_amount(self) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            full_amount=10_000,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            payload=pack(9_900, 'nat'),
            timestamp=setup.valid_timestamp,
        )
        with self.assertRaises(MichelsonError) as err:
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
                xtz_amount=10_000,
            ).send()
        assert "Tezos amount is not valid" in str(err.exception)

    def test_rejects_xtz_withdrawal_purchase_with_wrong_ticket_content(self) -> None:
        setup = self.fast_withdrawal_setup()

        # Wrong `token_id` but correct `token_info` case:
        wrong_token_id_content = TicketContent(42, None)
        with self.assertRaises(MichelsonError) as err:
            withdrawal = Withdrawal.default_with(
                full_amount=1,
                ticketer=setup.xtz_ticketer,
                content=wrong_token_id_content,
                payload=pack(1, 'nat'),
            )
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
                xtz_amount=1,
            ).send()
        assert "Wrong ticket content for xtz ticketer" in str(err.exception)

        # Wrong `token_info` but correct `token_id` case:
        wrong_payload_content = TicketContent(0, bytes(10))
        with self.assertRaises(MichelsonError) as err:
            withdrawal = Withdrawal.default_with(
                full_amount=1,
                ticketer=setup.xtz_ticketer,
                content=wrong_payload_content,
                payload=pack(1, 'nat'),
            )
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
                xtz_amount=1,
            ).send()
        assert "Wrong ticket content for xtz ticketer" in str(err.exception)

    def test_should_reject_settlement_with_attached_xtz(self) -> None:
        setup = self.fast_withdrawal_setup()

        setup.xtz_ticketer.mint(setup.smart_rollup, 99).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.smart_rollup)

        with self.assertRaises(MichelsonError) as err:
            setup.smart_rollup.bulk(
                setup.tester.set_settle_withdrawal(
                    target=setup.fast_withdrawal,
                    withdrawal=Withdrawal.default(),
                    xtz_amount=99,
                ),
                ticket.transfer(setup.tester),
            ).send()
            self.bake_block()
        assert "XTZ_DEPOSIT_DISALLOWED" in str(err.exception)

    def test_should_reject_settlement_from_wrong_rollup_address(self) -> None:
        setup = self.fast_withdrawal_setup()
        unauthorized_tester = self.deploy_ticket_router_tester()
        wrong_sender = self.bootstrap_account()

        setup.xtz_ticketer.mint(wrong_sender, 99).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(wrong_sender)

        with self.assertRaises(MichelsonError) as err:
            wrong_sender.bulk(
                unauthorized_tester.set_settle_withdrawal(
                    target=setup.fast_withdrawal,
                    withdrawal=Withdrawal.default(),
                ),
                ticket.transfer(unauthorized_tester),
            ).send()
            self.bake_block()
        assert "Sender is not allowed to call this entrypoint" in str(err.exception)

    def test_should_pay_custom_provider_when_specified(self) -> None:
        setup = self.fast_withdrawal_setup()
        custom_provider = self.bootstrap_non_baker_account()
        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            full_amount=123,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            payload=pack(123, 'nat'),
            timestamp=setup.valid_timestamp,
        )

        # Calling payout_withdrawal from the service provider for the custom provider:
        setup.fast_withdrawal.using(setup.service_provider).payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=custom_provider,
            xtz_amount=123,
        ).send()
        self.bake_block()

        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.get_service_provider() == get_address(custom_provider)

        setup.xtz_ticketer.mint(setup.smart_rollup, 123).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.smart_rollup)

        custom_provider_balance = custom_provider.balance()
        setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        updated_balance = custom_provider.balance()
        assert updated_balance == custom_provider_balance + Decimal('0.000123')
        status = setup.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.is_finished()

        # TODO: consider making this test for FA cases

    def test_should_return_config_on_get_config_view(self) -> None:
        xtz_ticketer = self.bootstrap_account()
        smart_rollup = self.bootstrap_account()
        one_day = 24 * 60 * 60

        fast_withdrawal = self.deploy_fast_withdrawal(
            xtz_ticketer=xtz_ticketer,
            smart_rollup=smart_rollup,
            expiration_seconds=one_day,
        )

        config = fast_withdrawal.get_config_view()
        assert config['expiration_seconds'] == one_day
        assert config['smart_rollup'] == get_address(smart_rollup)
        assert config['xtz_ticketer'] == get_address(xtz_ticketer)
        # TODO: add other config parameters checks if added

    def test_rejects_future_timestamp(self) -> None:
        setup = self.fast_withdrawal_setup()

        with self.assertRaises(MichelsonError) as err:
            withdrawal = Withdrawal.default_with(
                timestamp=setup.future_timestamp,
            )
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.service_provider,
            ).send()
        assert "Withdrawal must not have a future timestamp" in str(err.exception)

    def test_should_emit_events_on_payout_withdrawal_and_finalization(self) -> None:
        setup = self.fast_withdrawal_setup()
        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.withdrawer,
            full_amount=414,
            ticketer=setup.xtz_ticketer,
            content=TicketContent(0, None),
            payload=pack(414, 'nat'),
            timestamp=setup.valid_timestamp,
        )

        # Checking that the payout_withdrawal entrypoint emits the correct event:
        opg = setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=setup.service_provider,
            xtz_amount=414,
        ).send()
        self.bake_block()

        # Getting event from the last internal operation:
        result = self.find_call_result(opg)
        event_operation = result.operations[-1]  # type: ignore
        event = decode_event(event_operation)
        assert tuple(event['withdrawal'].values()) == withdrawal.as_tuple()
        assert event['service_provider'] == get_address(setup.service_provider)
        assert event['payout_amount'] == 414
        assert event_operation['tag'] == 'payout_withdrawal'

        # Checking that finalization for paid withdrawal emits the correct event:
        setup.xtz_ticketer.mint(setup.smart_rollup, 414).send()
        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.smart_rollup)

        opg = setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Getting event from the ticket transfer last internal operation:
        result = self.find_call_result(opg, 1)
        internal_operations = result['metadata']['internal_operation_results']  # type: ignore
        event = decode_event(internal_operations[-1])
        assert tuple(event['withdrawal'].values()) == withdrawal.as_tuple()
        assert event['receiver'] == get_address(setup.service_provider)
        assert internal_operations[-1]['tag'] == 'settle_withdrawal'

        # Checking that finalization for not paid withdrawal emits the correct event:
        withdrawal.full_amount = 333
        withdrawal.payload = pack(333, 'nat')
        setup.xtz_ticketer.mint(setup.smart_rollup, 333).send()

        self.bake_block()
        ticket = setup.xtz_ticketer.read_ticket(setup.smart_rollup)

        opg = setup.smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Getting event from the ticket transfer last internal operation:
        result = self.find_call_result(opg, 1)
        internal_operations = result['metadata']['internal_operation_results']  # type: ignore
        event = decode_event(internal_operations[-1])
        assert tuple(event['withdrawal'].values()) == withdrawal.as_tuple()
        assert event['receiver'] == get_address(setup.withdrawer)
        assert internal_operations[-1]['tag'] == 'settle_withdrawal'
