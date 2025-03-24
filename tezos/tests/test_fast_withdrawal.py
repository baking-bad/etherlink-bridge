from dataclasses import dataclass
from decimal import Decimal
from pytezos.client import PyTezosClient
from pytezos.rpc.errors import MichelsonError
from scripts.helpers.contracts.exchanger import Exchanger
from scripts.helpers.contracts.fast_withdrawal import FastWithdrawal, Withdrawal
from scripts.helpers.contracts.ticket_router_tester import TicketRouterTester
from scripts.helpers.contracts.tokens.token import TokenHelper
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

    def test_should_create_withdrawal_record_after_xtz_withdrawal_purchased(
        self,
    ) -> None:
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
        ).send()
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # TODO: check ticketer content is (0, None)

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
            ).send()
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
        ).send()
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
        ).send()
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
        ).send()
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
        ).send()
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
        ).send()
        self.bake_block()

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # TODO:
        # - check new key is added for transaction with different `ticketer`
        # - check new key is added for transaction with different ticket `content`

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
        ).send()
        self.bake_block()

        with self.assertRaises(MichelsonError) as err:
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=setup.alice,
                xtz_amount=1_000_000,
            ).send()
        assert "The fast withdrawal was already payed" in str(err.exception)

        # TODO: the same check for same provider (setup.manager)

    def test_provider_receives_xtz_withdrawal_after_purchase(self) -> None:
        # TODO: add smart_rollup role
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
        ).send()
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

        # Settle withdrawal: (sending ticket to the fast withdrawal
        # contract `default` entrypoint):
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

    def test_user_receives_xtz_withdrawal_when_no_purchase_made(self) -> None:
        # TODO: add smart_rollup role
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

    def test_provider_receives_fa2_withdrawal_after_purchase(self) -> None:
        setup = self.fast_withdrawal_setup()
        alice = setup.alice
        smart_rollup = self.bootstrap_account()
        provider = setup.manager

        token: TokenHelper = self.deploy_fa2(
            balances={provider: 1_000, smart_rollup: 1_000},
            token_id=33,
        )
        ticketer = self.deploy_ticketer(token, {})

        withdrawal = Withdrawal.default_with(
            full_amount=50,
            ticketer=ticketer,
            content=ticketer.read_content(),
            base_withdrawer=alice,
            payload=pack(30, 'nat'),
        )
        provider.bulk(
            token.allow(provider, setup.fast_withdrawal),
            setup.fast_withdrawal.payout_withdrawal(
                withdrawal=withdrawal,
                service_provider=provider,
            ),
        ).send()
        self.bake_block()
        assert token.get_balance(provider) == 1000 - 30
        assert token.get_balance(alice) == 30

        withdrawals_bigmap = setup.fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

        # Creating wrapped token (ticket) for smart_rollup:
        smart_rollup.bulk(
            token.allow(smart_rollup, ticketer),
            ticketer.deposit(50),
        ).send()
        self.bake_block()
        ticket = ticketer.read_ticket(smart_rollup)
        assert token.get_balance(smart_rollup) == 1000 - 50

        # Settle withdrawal: (sending ticket to the fast withdrawal
        # contract `default` entrypoint):
        smart_rollup.bulk(
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

        # Checking that the Provider received the token:
        assert token.get_balance(provider) == 1000 - 30 + 50

    def test_user_receives_fa12_withdrawal_when_no_purchase_made(self) -> None:
        setup = self.fast_withdrawal_setup()
        alice = setup.alice
        smart_rollup = self.bootstrap_account()

        token: TokenHelper = self.deploy_fa12(
            balances={smart_rollup: 100},
        )
        ticketer = self.deploy_ticketer(token, {})

        # Setting up withdrawal with Alice as a base withdrawer:
        withdrawal = Withdrawal.default_with(
            base_withdrawer=alice,
            ticketer=ticketer,
            content=TicketContent(0, None),
        )
        self.bake_block()

        # Creating wrapped token (ticket) for smart_rollup:
        smart_rollup.bulk(
            token.allow(smart_rollup, ticketer),
            ticketer.deposit(3),
        ).send()
        self.bake_block()
        ticket = ticketer.read_ticket(smart_rollup)
        assert token.get_balance(smart_rollup) == 100 - 3

        # No one purchased the withdrawal,
        # Sending ticket to the fast withdrawal contract `default` entrypoint:
        smart_rollup.bulk(
            setup.tester.set_settle_withdrawal(
                target=setup.fast_withdrawal,
                withdrawal=withdrawal,
            ),
            ticket.transfer(setup.tester),
        ).send()
        self.bake_block()

        # Checking that Alice received the token (full withdrawal amount):
        assert token.get_balance(alice) == 3
