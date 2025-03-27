from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, cast
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from pytezos.rpc.errors import MichelsonError
from scripts.helpers.contracts.ticketer import Ticketer
from scripts.helpers.contracts.xtz_ticketer import XtzTicketer
from scripts.helpers.contracts.fast_withdrawal import (
    Claimed,
    FastWithdrawal,
    Finished,
    Withdrawal,
)
from scripts.helpers.contracts.ticket_router_tester import TicketRouterTester
from scripts.helpers.contracts.tokens.token import TokenHelper
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
    fa12_withdrawal: Withdrawal
    fa12_token: TokenHelper
    fa12_ticketer: Ticketer
    fa2_withdrawal: Withdrawal
    fa2_token: TokenHelper
    fa2_ticketer: Ticketer


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

        token_balances: dict[Addressable, int] = {
            service_provider: 1_000_000,
            smart_rollup: 1_000_000,
        }

        fa12_token = self.deploy_fa12(token_balances)
        fa12_ticketer = self.deploy_ticketer(fa12_token, {})
        fa12_withdrawal = xtz_withdrawal.override(
            ticketer=fa12_ticketer,
            content=fa12_ticketer.read_content(),
        )

        fa2_token = self.deploy_fa2(token_balances, token_id=77)
        fa2_ticketer = self.deploy_ticketer(fa2_token, {})
        fa2_withdrawal = xtz_withdrawal.override(
            ticketer=fa2_ticketer,
            content=fa2_ticketer.read_content(),
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
            fa12_withdrawal=fa12_withdrawal,
            fa2_withdrawal=fa2_withdrawal,
            fa12_token=fa12_token,
            fa2_token=fa2_token,
            fa12_ticketer=fa12_ticketer,
            fa2_ticketer=fa2_ticketer,
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

    def make_fa12_ticket(
        self,
        test_env: FastWithdrawalTestEnvironment,
        amount: int,
        account: Optional[PyTezosClient] = None,
    ) -> Ticket:
        # NOTE: account should have FA1.2 tokens on their balance
        account = account or test_env.smart_rollup

        # Creating FA1.2 ticket for receiver
        account.bulk(
            test_env.fa12_token.allow(account, test_env.fa12_ticketer),
            test_env.fa12_ticketer.deposit(amount),
        ).send()
        self.bake_block()
        return test_env.fa12_ticketer.read_ticket(account)

    def make_fa2_ticket(
        self,
        test_env: FastWithdrawalTestEnvironment,
        amount: int,
        account: Optional[PyTezosClient] = None,
    ) -> Ticket:
        # NOTE: account should have FA2 tokens on their balance
        account = account or test_env.smart_rollup

        # Creating FA2 ticket for receiver
        account.bulk(
            test_env.fa2_token.allow(account, test_env.fa2_ticketer),
            test_env.fa2_ticketer.deposit(amount),
        ).send()
        self.bake_block()
        return test_env.fa2_ticketer.read_ticket(account)

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

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

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

            status = fast_withdrawal.get_service_provider_view(withdrawal)
            assert status.unwrap() == Claimed(provider)

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

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

        # Changing timestamp and paying the second withdrawal:
        withdrawal.timestamp = test_env.valid_timestamp + 1
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

        # Changing base_withdrawer and paying the third withdrawal:
        withdrawal.base_withdrawer = self.bootstrap_account()
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

        # Changing payload and paying the fourth withdrawal:
        discounted_amount = 777_000
        withdrawal.payload = pack(discounted_amount, 'nat')
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

        # Changing l2_caller and paying the fifth withdrawal:
        withdrawal.l2_caller = bytes.fromhex('ab' * 20)
        fast_withdrawal.payout_withdrawal(
            withdrawal, provider, discounted_amount
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

        # Changing ticketer and content and paying the sixth withdrawal:
        withdrawal.ticketer = test_env.fa12_withdrawal.ticketer
        withdrawal.content = test_env.fa12_withdrawal.content

        provider.bulk(
            test_env.fa12_token.allow(provider, fast_withdrawal),
            test_env.fast_withdrawal.payout_withdrawal(withdrawal, provider),
        ).send()
        self.bake_block()

        status = test_env.fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

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
        assert "The fast withdrawal was already payed" in str(err.exception)

        # Checking that the same withdrawal can't be paid again by the same provider:
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(withdrawal, provider, xtz_amount).send()
        assert "The fast withdrawal was already payed" in str(err.exception)

        # Check that the same withdrawal can't be paid again after it was finalized
        ticket = self.make_xtz_ticket(test_env, xtz_amount)
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=another_provider,
                xtz_amount=xtz_amount,
            ).send()
        assert "The fast withdrawal was already payed" in str(err.exception)

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

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

        # Recording the provider's balance before the withdrawal finalization:
        provider_balance = provider.balance()
        ticket = self.make_xtz_ticket(test_env, 77)
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        # Checking that status is now Finished:
        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Finished()

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

    def test_provider_receives_fa2_withdrawal_after_purchase(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        fast_withdrawal = test_env.fast_withdrawal
        provider = test_env.service_provider
        withdrawer = test_env.withdrawer
        token = test_env.fa2_token
        provider_balance = token.get_balance(provider)

        withdrawal = test_env.fa2_withdrawal.override(
            full_amount=50,
            payload=pack(30, 'nat'),
        )
        provider.bulk(
            token.allow(provider, fast_withdrawal),
            fast_withdrawal.payout_withdrawal(withdrawal, provider),
        ).send()
        self.bake_block()
        assert token.get_balance(provider) == provider_balance - 30
        assert token.get_balance(withdrawer) == 30

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)

        # Creating wrapped token (ticket) for smart_rollup:
        ticket = self.make_fa2_ticket(test_env, 50)
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        # Checking that status is now Finished:
        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Finished()

        # Checking that the provider received the token:
        assert token.get_balance(provider) == provider_balance - 30 + 50

    def test_user_receives_fa12_withdrawal_when_no_purchase_made(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        withdrawal = test_env.fa12_withdrawal
        withdrawer = test_env.withdrawer
        token = test_env.fa12_token

        # No one purchased the withdrawal, ticket received from the smart rollup:
        ticket = self.make_fa12_ticket(test_env, 3)
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        # Checking that withdrawer received the token (full withdrawal amount):
        assert token.get_balance(withdrawer) == 3

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

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(provider)
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
        assert "Tezos amount is not valid" in str(err.exception)

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
        assert "Tezos amount is not valid" in str(err.exception)

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
        assert "Wrong ticket content for xtz ticketer" in str(err.exception)

        # Wrong `token_info` but correct `token_id` case:
        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(
                withdrawal=wrong_payload_content_withdrawal,
                service_provider=provider,
                xtz_amount=1,
            ).send()
        assert "Wrong ticket content for xtz ticketer" in str(err.exception)

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
        wrong_sender = self.bootstrap_account()

        ticket = self.make_xtz_ticket(test_env, 99, wrong_sender)

        with self.assertRaises(MichelsonError) as err:
            wrong_sender.bulk(
                unauthorized_tester.set_settle_withdrawal(
                    target=test_env.fast_withdrawal,
                    withdrawal=test_env.xtz_withdrawal,
                ),
                ticket.transfer(unauthorized_tester),
            ).send()
            self.bake_block()
        assert "Sender is not allowed to call this entrypoint" in str(err.exception)

    def test_should_pay_custom_provider_when_specified(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        custom_provider = self.bootstrap_non_baker_account()
        fast_withdrawal = test_env.fast_withdrawal
        provider = test_env.service_provider
        withdrawal = test_env.xtz_withdrawal.override(
            full_amount=123,
            payload=pack(123, 'nat'),
        )

        # Calling payout_withdrawal from the service provider for the custom provider:
        fast_withdrawal.using(provider).payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=custom_provider,
            xtz_amount=123,
        ).send()
        self.bake_block()

        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Claimed(custom_provider)

        # Recording the custom provider's balance before the withdrawal finalization:
        ticket = self.make_xtz_ticket(test_env, 123)
        custom_provider_balance = custom_provider.balance()
        self.finalize_withdrawal(test_env, withdrawal, ticket)

        updated_balance = custom_provider.balance()
        assert updated_balance == custom_provider_balance + Decimal('0.000123')
        status = fast_withdrawal.get_service_provider_view(withdrawal)
        assert status.unwrap() == Finished()

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

    def test_rejects_future_timestamp(self) -> None:
        test_env = self.setup_fast_withdrawal_test_environment()
        provider = test_env.service_provider
        fast_withdrawal = test_env.fast_withdrawal
        withdrawal = test_env.xtz_withdrawal.override(
            timestamp=test_env.future_timestamp,
        )

        with self.assertRaises(MichelsonError) as err:
            fast_withdrawal.payout_withdrawal(withdrawal, provider).send()
        assert "Withdrawal must not have a future timestamp" in str(err.exception)

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
