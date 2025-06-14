from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, cast
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from pytezos.rpc.errors import MichelsonError
from scripts.helpers.contracts.xtz_ticketer import XtzTicketer
from scripts.helpers.contracts.fast_withdrawal import (
    PaidOut,
    FastWithdrawal,
    Cemented,
    Withdrawal,
)
from scripts.helpers.contracts.ticket_router_tester import TicketRouterTester
from scripts.helpers.ticket import Ticket
from scripts.helpers.ticket_content import TicketContent
from scripts.helpers.utility import pack
from tezos.tests.base import BaseTestCase
from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.utility import decode_event


@dataclass
class FastWithdrawalTestEnvironment:
    manager: PyTezosClient
    withdrawer: PyTezosClient
    smart_rollup: PyTezosClient
    service_provider: PyTezosClient
    fast_withdrawal: FastWithdrawal
    tester: TicketRouterTester
    valid_timestamp: int
    expired_timestamp: int
    future_timestamp: int
    xtz_ticketer: XtzTicketer
    xtz_withdrawal: Withdrawal


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

    def setup_fast_withdrawal_test_environment(
        self,
    ) -> FastWithdrawalTestEnvironment:
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
        valid_timestamp = self.manager.now()

        xtz_withdrawal = Withdrawal(
            withdrawal_id=0,
            base_withdrawer=withdrawer,
            payload=pack(1_000_000, 'nat'),
            ticketer=xtz_ticketer,
            content=TicketContent(0, None),
            timestamp=valid_timestamp,
            full_amount=1_000_000,
            l2_caller=bytes(20),
        )

        return FastWithdrawalTestEnvironment(
            manager=self.manager,
            withdrawer=withdrawer,
            service_provider=service_provider,
            smart_rollup=smart_rollup,
            xtz_ticketer=xtz_ticketer,
            fast_withdrawal=fast_withdrawal,
            tester=tester,
            valid_timestamp=valid_timestamp,
            expired_timestamp=self.manager.now() - one_day - 1,
            future_timestamp=self.manager.now() + one_day,
            xtz_withdrawal=xtz_withdrawal,
        )

    def make_xtz_ticket(
        self,
        test_env: FastWithdrawalTestEnvironment,
        amount: int,
        account: Optional[PyTezosClient] = None,
    ) -> Ticket:
        # Minting xtz ticket for the account (smart rollup by default):
        account = account or test_env.smart_rollup
        test_env.xtz_ticketer.mint(account, amount).send()
        self.bake_block()
        ticket = test_env.xtz_ticketer.read_ticket(account)
        return ticket

    def finalize_withdrawal(
        self,
        test_env: FastWithdrawalTestEnvironment,
        withdrawal: Withdrawal,
        ticket: Ticket,
    ) -> OperationGroup:
        # Settle withdrawal: (sending ticket to the fast withdrawal
        # contract `default` entrypoint):
        opg = test_env.smart_rollup.bulk(
            test_env.tester.set_settle_withdrawal(
                target=test_env.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(test_env.tester),
        ).send()
        self.bake_block()
        return opg

    def test_should_create_withdrawal_record_after_xtz_withdrawal_purchased(
        self,
    ) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        xtz_amount = 1_000_000
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=xtz_amount,
            payload=pack(xtz_amount, 'nat'),
        )

        fast_withdrawal.payout_withdrawal(withdrawal, provider, xtz_amount).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)

    def test_should_accept_different_payloads_for_different_ticket_amounts(
        self,
    ) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal

        # NOTE: the manager account balance is 3.7 million xtz
        amounts = [1, 17, 1_000_000_000_000]

        for amount in amounts:
            withdrawal = test_env.xtz_withdrawal.override(
                full_amount=amount,
                payload=pack(amount, 'nat'),
            )
            fast_withdrawal.payout_withdrawal(withdrawal, provider, amount).send()
            self.bake_block()

            status = fast_withdrawal.get_status_view(withdrawal)
            assert status.unwrap() == PaidOut(provider)

    def test_should_create_different_withdrawal_records(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        discounted_amount = 999_500
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1_000_000,
            payload=pack(999_500, 'nat'),
        )

        # Creating the first withdrawal record:
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)

        # Changing timestamp and paying the second withdrawal:
        withdrawal.timestamp = test_env.valid_timestamp + 1
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)

        # Changing base_withdrawer and paying the third withdrawal:
        withdrawal.base_withdrawer = self.bootstrap_account()
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)

        # Changing payload and paying the fourth withdrawal:
        discounted_amount = 777_000
        withdrawal.payload = pack(discounted_amount, 'nat')
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)

        # Changing l2_caller and paying the fifth withdrawal:
        withdrawal.l2_caller = bytes.fromhex('ab' * 20)
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)

    def test_should_reject_duplicate_withdrawal(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        xtz_amount = 1_000_000
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=xtz_amount,
            payload=pack(xtz_amount, 'nat'),
        )

        fast_withdrawal.payout_withdrawal(withdrawal, provider, xtz_amount).send()
        self.bake_block()

        # Checking that the same withdrawal can't be paid again by another provider:
        another_provider = self.bootstrap_account()
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal, another_provider, xtz_amount
            ).send()
        assert "DUPLICATE_WITHDRAWAL_PAYOUT" in str(err.exception)

        # Checking that the same withdrawal can't be paid again by the same provider:
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(withdrawal, provider, xtz_amount).send()
        assert "DUPLICATE_WITHDRAWAL_PAYOUT" in str(err.exception)

        # Check that the same withdrawal can't be paid again after it was finalized
        ticket = self.make_xtz_ticket(test_env, xtz_amount)
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=another_provider,
                xtz_amount=xtz_amount,
            ).send()
        assert "DUPLICATE_WITHDRAWAL_PAYOUT" in str(err.exception)

    def test_provider_receives_xtz_withdrawal_after_purchase(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=77,
            payload=pack(77, 'nat'),
        )

        fast_withdrawal.payout_withdrawal(
            withdrawal,
            provider,
            xtz_amount=77,
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)

        # Recording the provider's balance before the withdrawal finalization:
        provider_balance = provider.balance()
        ticket = self.make_xtz_ticket(test_env, 77)
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        # Checking that status is now Cemented:
        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == Cemented()

        # Checking that the provider received the xtz:
        assert provider.balance() == provider_balance + Decimal('0.000077')

    def test_user_receives_xtz_withdrawal_when_no_purchase_made(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        withdrawer = test_env.withdrawer
        withdrawer_balance = withdrawer.balance()

        ticket = self.make_xtz_ticket(test_env, 333)
        self.finalize_withdrawal(test_env, test_env.xtz_withdrawal, ticket)

        # Checking that withdrawer received the xtz (full withdrawal amount):
        assert withdrawer.balance() == withdrawer_balance + Decimal('0.000333')

    def test_should_allow_xtz_withdrawal_purchase_at_full_price_after_timestamp_expired(
        self,
    ) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        withdrawer = test_env.withdrawer
        provider = test_env.service_provider
        withdrawer_balance = withdrawer.balance()
        fast_withdrawal = test_env.fast_withdrawal

        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1_000,
            payload=pack(990, 'nat'),
            timestamp=test_env.expired_timestamp,
        )

        test_env.fast_withdrawal.payout_withdrawal(
            withdrawal,
            provider,
            xtz_amount=1_000,
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_status_view(withdrawal)
        assert status.unwrap() == PaidOut(provider)
        assert withdrawer.balance() == withdrawer_balance + Decimal('0.001000')

        # Creating wrapped xtz ticket for Smart Rollup:
        ticket = self.make_xtz_ticket(test_env, 1_000)
        provider_balance = provider.balance()
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        assert provider.balance() == provider_balance + Decimal('0.001000')

    def test_rejects_xtz_withdrawal_purchase_at_discounted_price_if_expired(
        self,
    ) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal

        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1_000,
            payload=pack(990, 'nat'),
            timestamp=test_env.expired_timestamp,
        )
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal,
                provider,
                xtz_amount=990,
            ).send()
        assert "INVALID_XTZ_AMOUNT" in str(err.exception)

    def test_should_reject_xtz_withdrawal_purchase_with_wrong_xtz_amount(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal

        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=10_000,
            payload=pack(9_900, 'nat'),
        )
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal,
                provider,
                xtz_amount=10_000,
            ).send()
        assert "INVALID_XTZ_AMOUNT" in str(err.exception)

    def test_rejects_xtz_withdrawal_purchase_with_wrong_ticket_content(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        wrong_token_id_withdrawal = test_env.xtz_withdrawal.override(
            content=TicketContent(42, None),
            payload=pack(1, 'nat'),
        )
        wrong_payload_content_withdrawal = test_env.xtz_withdrawal.override(
            content=TicketContent(0, bytes(10)),
            payload=pack(1, 'nat'),
        )

        # Wrong `token_id` but correct `token_info` case:
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal=wrong_token_id_withdrawal,
                service_provider=provider,
                xtz_amount=1,
            ).send()
        assert "WRONG_XTZ_CONTENT" in str(err.exception)

        # Wrong `token_info` but correct `token_id` case:
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal=wrong_payload_content_withdrawal,
                service_provider=provider,
                xtz_amount=1,
            ).send()
        assert "WRONG_XTZ_CONTENT" in str(err.exception)

    def test_should_reject_settlement_with_attached_xtz(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        smart_rollup = test_env.smart_rollup
        ticket = self.make_xtz_ticket(test_env, 99)

        with self.assertRaises(MichelsonError) as err:
            smart_rollup.bulk(
                test_env.tester.set_settle_withdrawal(
                    target=test_env.fast_withdrawal,
                    withdrawal=test_env.xtz_withdrawal,
                    xtz_amount=99,
                ),
                ticket.transfer(test_env.tester),
            ).send()
            self.bake_block()
        assert "XTZ_DEPOSIT_DISALLOWED" in str(err.exception)

    def test_should_reject_settlement_from_wrong_rollup_address(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        unauthorized_tester = self.deploy_ticket_router_tester()
        arbitrary_account = self.bootstrap_account()

        ticket = self.make_xtz_ticket(test_env, 99, arbitrary_account)

        with self.assertRaises(MichelsonError) as err:
            arbitrary_account.bulk(
                unauthorized_tester.set_settle_withdrawal(
                    target=test_env.fast_withdrawal,
                    withdrawal=test_env.xtz_withdrawal,
                ),
                ticket.transfer(unauthorized_tester),
            ).send()
            self.bake_block()
        assert "SENDER_NOT_ALLOWED" in str(err.exception)

    def test_should_pay_custom_provider_when_specified(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        custom_provider = self.bootstrap_non_baker_account()
        fast_withdrawal = test_env.fast_withdrawal
        provider = test_env.service_provider

        xtz_withdrawal = test_env.xtz_withdrawal.override(
            full_amount=123,
            payload=pack(123, 'nat'),
        )

        # Calling payout_withdrawal from the service provider for the custom provider:
        provider.bulk(
            fast_withdrawal.payout_withdrawal(
                withdrawal=xtz_withdrawal,
                service_provider=custom_provider,
                xtz_amount=123,
            ),
        ).send()
        self.bake_block()

        xtz_status = fast_withdrawal.get_status_view(xtz_withdrawal)

        assert xtz_status.unwrap() == PaidOut(custom_provider)

        # Finalizing the xtz withdrawal:
        ticket = self.make_xtz_ticket(test_env, 123)
        custom_provider_balance = custom_provider.balance()
        self.finalize_withdrawal(test_env, xtz_withdrawal, ticket)

        updated_balance = custom_provider.balance()
        assert updated_balance == custom_provider_balance + Decimal('0.000123')
        assert fast_withdrawal.get_status_view(xtz_withdrawal).unwrap() == Cemented()

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

    def test_rejects_future_timestamp(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            timestamp=test_env.future_timestamp,
        )

        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(withdrawal, provider).send()
        assert "TIMESTAMP_IN_FUTURE" in str(err.exception)

    def test_should_emit_events_on_payout_withdrawal_and_finalization(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawer = test_env.withdrawer
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=414,
            payload=pack(414, 'nat'),
        )

        # Checking that the payout_withdrawal entrypoint emits the correct event:
        opg = fast_withdrawal.payout_withdrawal(
            withdrawal,
            provider,
            xtz_amount=414,
        ).send()
        self.bake_block()

        # Getting event from the last internal operation:
        result = self.find_call_result(opg)
        event_operation = result.operations[-1]  # type: ignore
        event = decode_event(event_operation)
        assert tuple(event['withdrawal'].values()) == withdrawal.as_tuple()
        assert event['service_provider'] == get_address(provider)
        assert event['payout_amount'] == 414
        assert event_operation['tag'] == 'payout_withdrawal'

        # Checking that finalization for paid withdrawal emits the correct event:
        ticket = self.make_xtz_ticket(test_env, 414)
        opg = self.finalize_withdrawal(test_env, withdrawal, ticket)

        # Getting event from the ticket transfer last internal operation:
        result = self.find_call_result(opg, 1)
        internal_operations = result['metadata']['internal_operation_results']  # type: ignore
        event = decode_event(internal_operations[-1])
        assert tuple(event['withdrawal'].values()) == withdrawal.as_tuple()
        assert event['receiver'] == get_address(provider)
        assert internal_operations[-1]['tag'] == 'settle_withdrawal'

        # Checking that finalization for not paid withdrawal emits the correct event:
        withdrawal = withdrawal.override(
            full_amount=333,
            payload=pack(333, 'nat'),
        )
        ticket = self.make_xtz_ticket(test_env, 333)
        opg = self.finalize_withdrawal(test_env, withdrawal, ticket)

        # Getting event from the ticket transfer last internal operation:
        result = self.find_call_result(opg, 1)
        internal_operations = result['metadata']['internal_operation_results']  # type: ignore
        event = decode_event(internal_operations[-1])
        assert tuple(event['withdrawal'].values()) == withdrawal.as_tuple()
        assert event['receiver'] == get_address(withdrawer)
        assert internal_operations[-1]['tag'] == 'settle_withdrawal'

    def test_rejects_if_l2_caller_is_not_20_bytes_long(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1_000,
            payload=pack(1_000, 'nat'),
            l2_caller=bytes(10),
        )

        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal,
                provider,
                xtz_amount=1_000,
            ).send()
            self.bake_block()
        assert "WRONG_L2_CALLER_LENGTH" in str(err.exception)

    def test_rejects_invalid_payload(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1_000,
            payload=pack('wrong-payload', 'string'),
        )

        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal,
                provider,
                xtz_amount=1_000,
            ).send()
            self.bake_block()
        assert "PAYLOAD_UNPACK_FAILED" in str(err.exception)

    def test_non_native_tickets_not_supported_for_payout(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1_000,
            payload=pack(1_000, 'nat'),
            ticketer=self.bootstrap_account(),
        )

        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(withdrawal, provider).send()
        assert "ONLY_XTZ_WITHDRAWALS_ARE_SUPPORTED" in str(err.exception)

    def test_non_xtz_tickets_redirected_to_withdrawer_on_settlement(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=471,
            payload=pack(471, 'nat'),
            ticketer=test_env.tester,
            content=TicketContent(0, "some-ticket-content".encode()),
        )

        test_env.smart_rollup.bulk(
            test_env.tester.set_settle_withdrawal(
                target=test_env.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            test_env.tester.mint(
                content=TicketContent(0, "some-ticket-content".encode()),
                amount=471,
            ),
        ).send()
        self.bake_block()

        # Checking that the withdrawer received the ticket:
        ticket = Ticket.create(
            client=test_env.withdrawer,
            owner=test_env.withdrawer,
            ticketer=get_address(test_env.tester),
            content=TicketContent(0, "some-ticket-content".encode()),
        )
        assert ticket.amount == 471

        # Checking that no withdrawal record was created:
        assert test_env.fast_withdrawal.get_status_view(withdrawal).is_none()

    def test_reject_cemented_withdrawal(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1991,
            payload=pack(1991, 'nat'),
        )

        fast_withdrawal.payout_withdrawal(
            withdrawal,
            provider,
            xtz_amount=1991,
        ).send()
        self.bake_block()

        ticket = self.make_xtz_ticket(test_env, 1991)
        self.finalize_withdrawal(test_env, withdrawal, ticket)
        assert fast_withdrawal.get_status_view(withdrawal).unwrap() == Cemented()

        # Executing same withdrawal finalization for the second time:
        with self.assertRaises(MichelsonError) as err:
            ticket = self.make_xtz_ticket(test_env, 1991)
            self.finalize_withdrawal(test_env, withdrawal, ticket)
        assert "UNEXPECTED_CEMENTED_WITHDRAWAL" in str(err.exception)

    def test_reject_if_payout_exceeds_full_amount(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=1_000,
            payload=pack(1_001, 'nat'),
        )
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal,
                provider,
                xtz_amount=1_001,
            ).send()
        assert "PAYOUT_EXCEEDS_FULL_AMOUNT" in str(err.exception)
