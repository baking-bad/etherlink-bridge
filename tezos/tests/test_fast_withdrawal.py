from dataclasses import dataclass
from typing import Tuple
from pytezos.client import PyTezosClient
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
    ) -> tuple[PyTezosClient, Exchanger, FastWithdrawal, ServiceProvider]:

        alice = self.bootstrap_account()
        exchanger = self.deploy_exchanger()
        fast_withdrawal = self.deploy_fast_withdrawal(exchanger, alice)
        service_provider = self.deploy_service_provider()
        return alice, exchanger, fast_withdrawal, service_provider

    def test_should_create_withdrawal_record_when_purchased(self) -> None:
        alice, exchanger, fast_withdrawal, service_provider = (
            self.fast_withdrawal_setup()
        )

        withdrawal = Withdrawal(
            withdrawal_id=0,
            withdrawal_amount=1_000_000,
            base_withdrawer=alice,
            timestamp=0,
            payload=pack(1_000_000, 'nat'),
            l2_caller=bytes(20),
        )

        provider = self.manager
        service_provider.purchase_withdrawal_proxy(
            fast_withdrawal,
            exchanger,
            withdrawal.withdrawal_id,
            withdrawal.base_withdrawer,
            withdrawal.timestamp,
            provider,
            withdrawal.payload,
            withdrawal.l2_caller,
            withdrawal.withdrawal_amount,
            xtz_amount=withdrawal.withdrawal_amount,
        ).send()
        self.bake_block()

        withdrawals_bigmap = fast_withdrawal.contract.storage['withdrawals']
        stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
        assert stored_address == get_address(provider)

    def test_should_correctly_encode_payloads_for_different_ticket_amounts(
        self,
    ) -> None:
        alice, exchanger, fast_withdrawal, service_provider = (
            self.fast_withdrawal_setup()
        )

        # NOTE: the manager account balance is 3.7 million xtz
        amounts = [1, 17, 1_000_000_000_000]

        for amount in amounts:
            withdrawal = Withdrawal(
                withdrawal_id=0,
                withdrawal_amount=amount,
                base_withdrawer=alice,
                timestamp=0,
                payload=pack(amount, 'nat'),
                l2_caller=bytes(20),
            )

            provider = self.manager
            service_provider.purchase_withdrawal_proxy(
                fast_withdrawal,
                exchanger,
                withdrawal.withdrawal_id,
                withdrawal.base_withdrawer,
                withdrawal.timestamp,
                provider,
                withdrawal.payload,
                withdrawal.l2_caller,
                withdrawal.withdrawal_amount,
                xtz_amount=withdrawal.withdrawal_amount,
            ).send()
            self.bake_block()

            withdrawals_bigmap = fast_withdrawal.contract.storage['withdrawals']
            stored_address = withdrawals_bigmap[withdrawal.as_tuple()]()  # type: ignore
            assert stored_address == get_address(provider)
