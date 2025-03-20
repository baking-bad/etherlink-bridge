from dataclasses import dataclass
from decimal import Decimal
from pytezos.client import PyTezosClient
from pytezos.rpc.errors import MichelsonError
from scripts.helpers.contracts.exchanger import Exchanger
from scripts.helpers.contracts.fast_withdrawal import FastWithdrawal, Withdrawal
from scripts.helpers.contracts.ticket_router_tester import TicketRouterTester
from scripts.helpers.ticket_content import TicketContent
from scripts.helpers.utility import pack
from tezos.tests.base import BaseTestCase
from scripts.helpers.addressable import Addressable, get_address


@dataclass
class FastWithdrawalTestSetup:
    manager: PyTezosClient
    alice: PyTezosClient
    exchanger: Exchanger
    fast_withdrawal: FastWithdrawal
    tester: TicketRouterTester


class FastWithdrawalTestCase(BaseTestCase):
    def deploy_fast_withdrawal(
        self,
        exchanger: Addressable,
        smart_rollup: Addressable,
    ) -> FastWithdrawal:
        """Deploys FastWithdrawal contract for the specified exchanger and
        smart_rollup addresses"""

        opg = FastWithdrawal.originate(self.manager, exchanger, smart_rollup).send()
        self.bake_block()
        return FastWithdrawal.from_opg(self.manager, opg)

    def deploy_exchanger(
        self,
    ) -> Exchanger:
        """Deploys Exchanger (native xtz ticketer) contract"""

        opg = Exchanger.originate(self.manager).send()
        self.bake_block()
        return Exchanger.from_opg(self.manager, opg)

    def fast_withdrawal_setup(
        self,
    ) -> FastWithdrawalTestSetup:
        alice = self.bootstrap_account()
        exchanger = self.deploy_exchanger()
        tester = self.deploy_ticket_router_tester()
        fast_withdrawal = self.deploy_fast_withdrawal(exchanger, tester)

        return FastWithdrawalTestSetup(
            manager=self.manager,
            alice=alice,
            exchanger=exchanger,
            fast_withdrawal=fast_withdrawal,
            tester=tester,
        )

    def test_should_create_withdrawal_record_when_purchased(self) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.alice,
            payload=pack(1_000_000, 'nat'),
            ticketer=setup.exchanger,
            content=TicketContent(0, None),
        )
        provider = self.manager
        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=provider,
            xtz_amount=1_000_000,
        )
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

    def test_should_correctly_encode_payloads_for_different_ticket_amounts(
        self,
    ) -> None:
        setup = self.fast_withdrawal_setup()

        # NOTE: the manager account balance is 3.7 million xtz
        amounts = [1, 17, 1_000_000_000_000]

        for amount in amounts:
            withdrawal = Withdrawal.default_with(
                full_amount=amount,
                ticketer=setup.exchanger,
                content=TicketContent(0, None),
                base_withdrawer=setup.alice,
                payload=pack(amount, 'nat'),
            )

            provider = self.manager
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=provider,
                xtz_amount=amount,
            )
            self.bake_block()

            withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
            stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
            assert stored_address == get_address(provider)

    def test_should_create_different_withdrawal_records(self) -> None:
        setup = self.fast_withdrawal_setup()
        provider = self.manager

        withdrawal = Withdrawal(
            withdrawal_id=1000,
            full_amount=1_000_000,
            ticketer=setup.exchanger,
            content=TicketContent(0, None),
            base_withdrawer=setup.alice,
            timestamp=0,
            payload=pack(999_500, 'nat'),
            l2_caller=bytes(20),
        )

        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=provider,
            xtz_amount=999_500,
        )
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # Changing timestamp:
        withdrawal.timestamp = 12345
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=provider,
            withdrawal=withdrawal,
            xtz_amount=999_500,
        )
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # Changing base_withdrawer:
        withdrawal.base_withdrawer = self.bootstrap_account()
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=provider,
            withdrawal=withdrawal,
            xtz_amount=999_500,
        )
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # Changing payload:
        withdrawal.payload = pack(777_000, 'nat')
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=provider,
            withdrawal=withdrawal,
            xtz_amount=777_000,
        )
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # Changing l2_caller:
        withdrawal.l2_caller = bytes.fromhex('ab' * 20)
        setup.fast_withdrawal.payout_withdrawal(
            service_provider=provider,
            withdrawal=withdrawal,
            xtz_amount=777_000,
        )
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

    def test_should_reject_duplicate_withdrawal(self) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            ticketer=setup.exchanger,
            content=TicketContent(0, None),
            payload=pack(1_000_000, 'nat'),
        )
        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=setup.manager,
            xtz_amount=1_000_000,
        )
        self.bake_block()

        with self.assertRaises(MichelsonError) as err:
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.alice,
                xtz_amount=1_000_000,
            )
        assert "The fast withdrawal was already payed" in str(err.exception)

    def test_provider_receives_withdrawal_when_purchased(self) -> None:
        setup = self.fast_withdrawal_setup()

        provider = setup.manager
        withdrawal = Withdrawal.default_with(
            full_amount=77,
            ticketer=setup.exchanger,
            content=TicketContent(0, None),
            payload=pack(77, 'nat'),
        )
        setup.fast_withdrawal.payout_withdrawal(
            withdrawal=withdrawal,
            service_provider=provider,
            xtz_amount=77,
        )
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # Creating wrapped xtz ticket for Alice:
        setup.exchanger.mint(setup.alice, 77).send()
        self.bake_block()
        ticket = setup.exchanger.read_ticket(setup.alice)

        # Recording providers balance:
        provider_balance = provider.balance()

        # Sending ticket to the fast withdrawal contract `default` entrypoint:
        setup.alice.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Checking that there is no record in the fast withdrawal contract:
        with self.assertRaises(KeyError):
            withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
            stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore

        # Checking that the provider received the xtz:
        assert provider.balance() == provider_balance + Decimal('0.000077')

    def test_user_receives_withdrawal_when_no_one_purchased(self) -> None:
        setup = self.fast_withdrawal_setup()
        alice_balance = setup.alice.balance()

        # Setting up withdrawal with Alice as a base withdrawer:
        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.alice,
            ticketer=setup.exchanger,
            content=TicketContent(0, None),
        )
        self.bake_block()

        # Creating wrapped xtz ticket:
        setup.exchanger.mint(setup.manager, 333).send()
        self.bake_block()
        ticket = setup.exchanger.read_ticket(setup.manager)

        # No one purchased the withdrawal,
        # Sending ticket to the fast withdrawal contract `default` entrypoint:
        setup.manager.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Checking that Alice received the xtz (full withdrawal amount):
        assert setup.alice.balance() == alice_balance + Decimal('0.000333')
