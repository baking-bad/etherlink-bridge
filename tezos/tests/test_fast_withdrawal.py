from dataclasses import dataclass
from typing import Optional, Tuple
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from pytezos.rpc.errors import MichelsonError
from scripts.helpers.contracts.exchanger import Exchanger
from scripts.helpers.contracts.fast_withdrawal import FastWithdrawal
from scripts.helpers.contracts.service_provider import ServiceProvider
from scripts.helpers.utility import pack
from tezos.tests.base import BaseTestCase
from scripts.helpers.addressable import Addressable, get_address


# TODO: consider moving Withdrawal to helpers/contracts?
@dataclass
class Withdrawal:
    withdrawal_id: int
    withdrawal_amount: int
    base_withdrawer: Addressable
    timestamp: int
    payload: bytes
    l2_caller: bytes

    # TODO: consider renaming to as_storage_key?
    def as_tuple(self) -> Tuple[int, int, str, int, bytes, bytes]:
        return (
            self.withdrawal_id,
            self.withdrawal_amount,
            get_address(self.base_withdrawer),
            self.timestamp,
            self.payload,
            self.l2_caller,
        )

    @classmethod
    def default_with(
        cls,
        withdrawal_id: int = 0,
        withdrawal_amount: int = 1_000_000,
        base_withdrawer: Addressable = "tz1KqTpEZ7Yob7QbPE4Hy4Wo8fHG8LhKxZSx",
        timestamp: int = 0,
        payload: bytes = pack(1_000_000, 'nat'),
        l2_caller: bytes = bytes(20),
    ) -> 'Withdrawal':
        """Creates a default Withdrawal object filled with default values"""

        return cls(
            withdrawal_id=withdrawal_id,
            withdrawal_amount=withdrawal_amount,
            base_withdrawer=base_withdrawer,
            timestamp=timestamp,
            payload=payload,
            l2_caller=l2_caller,
        )

    @classmethod
    def default(cls) -> 'Withdrawal':
        return cls.default_with()


@dataclass
class FastWithdrawalTestSetup:
    manager: PyTezosClient
    alice: PyTezosClient
    exchanger: Exchanger
    fast_withdrawal: FastWithdrawal
    service_provider: ServiceProvider

    def call_default_purchase_withdrawal_with(
        self,
        fast_withdrawal: Optional[FastWithdrawal] = None,
        exchanger: Optional[Exchanger] = None,
        service_provider: Optional[Addressable] = None,
        withdrawal: Optional[Withdrawal] = None,
        xtz_amount: Optional[int] = None,
    ) -> OperationGroup:
        """Calls purchase_withdrawal_proxy with default values"""

        fast_withdrawal = fast_withdrawal or self.fast_withdrawal
        exchanger = exchanger or self.exchanger
        service_provider = service_provider or self.service_provider
        withdrawal = withdrawal or Withdrawal.default()
        xtz_amount = xtz_amount or withdrawal.withdrawal_amount

        return self.service_provider.purchase_withdrawal_proxy(
            fast_withdrawal,
            exchanger,
            withdrawal.withdrawal_id,
            withdrawal.base_withdrawer,
            withdrawal.timestamp,
            service_provider,
            withdrawal.payload,
            withdrawal.l2_caller,
            withdrawal.withdrawal_amount,
            xtz_amount=xtz_amount,
        ).send()


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

    def deploy_service_provider(
        self,
    ) -> ServiceProvider:
        """Deploys ServiceProvider contract with a dummy storage"""

        opg = ServiceProvider.originate(self.manager).send()
        self.bake_block()
        return ServiceProvider.from_opg(self.manager, opg)

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
        fast_withdrawal = self.deploy_fast_withdrawal(exchanger, alice)
        service_provider = self.deploy_service_provider()
        return FastWithdrawalTestSetup(
            manager=self.manager,
            alice=alice,
            exchanger=exchanger,
            fast_withdrawal=fast_withdrawal,
            service_provider=service_provider,
        )

    def test_should_create_withdrawal_record_when_purchased(self) -> None:
        setup = self.fast_withdrawal_setup()

        withdrawal = Withdrawal.default_with(
            base_withdrawer=setup.alice,
        )
        provider = self.manager
        setup.call_default_purchase_withdrawal_with(
            service_provider=provider,
            withdrawal=withdrawal,
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
                withdrawal_amount=amount,
                base_withdrawer=setup.alice,
                payload=pack(amount, 'nat'),
            )

            provider = self.manager
            setup.call_default_purchase_withdrawal_with(
                service_provider=provider,
                withdrawal=withdrawal,
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
            withdrawal_amount=1_000_000,
            base_withdrawer=setup.alice,
            timestamp=0,
            payload=pack(999_500, 'nat'),
            l2_caller=bytes(20),
        )

        setup.call_default_purchase_withdrawal_with(
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
        setup.call_default_purchase_withdrawal_with(
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
        setup.call_default_purchase_withdrawal_with(
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
        setup.call_default_purchase_withdrawal_with(
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
        setup.call_default_purchase_withdrawal_with(
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

        withdrawal = Withdrawal.default()
        setup.call_default_purchase_withdrawal_with(
            withdrawal=withdrawal,
            service_provider=setup.manager,
        )
        self.bake_block()

        with self.assertRaises(MichelsonError) as err:
            setup.call_default_purchase_withdrawal_with(
                withdrawal=withdrawal,
                service_provider=setup.alice,
            )
        assert "The fast withdrawal was already payed" in str(err.exception)
