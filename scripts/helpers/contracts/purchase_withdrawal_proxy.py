from os.path import join
from typing import Any

from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup

from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.contracts.fast_withdrawal import Withdrawal
from scripts.helpers.utility import get_build_dir
from scripts.helpers.utility import originate_from_file


class PurchaseWithdrawalProxy(ContractHelper):
    @staticmethod
    def make_storage(
        dummy_address: Addressable,
    ) -> dict[str, Any]:
        """Creates a dummy storage for PurchaseWithdrawalProxy contract"""

        return {
            "withdrawal": {
                "withdrawal_id": 0,
                "full_amount": 0,
                "timestamp": 0,
                "base_withdrawer": dummy_address,
                "payload": bytes(0),
                "l2_caller": bytes(0),
            },
            "service_provider": dummy_address,
            "fast_withdrawal_contract": dummy_address,
            "exchanger": dummy_address,
        }

    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
    ) -> OperationGroup:
        """Deploys PurchaseWithdrawalProxy contract with a dummy storage"""

        storage = cls.make_storage(get_address(client))
        filename = join(get_build_dir(), "purchase-withdrawal-proxy.tz")
        return originate_from_file(filename, client, storage)

    def purchase_withdrawal_proxy(
        self,
        withdrawal: Withdrawal,
        service_provider: Addressable,
        fast_withdrawal_contract: Addressable,
        # TODO: consider making exchanger optional,
        #       it can be acquired from the fast_withdrawal_contract
        exchanger: Addressable,
        xtz_amount: int = 0,
    ) -> OperationGroup:
        """Creates an operation with call to the payout_proxy entrypoint"""

        return (
            self.contract.purchase_withdrawal_proxy(
                withdrawal.as_tuple(),
                get_address(service_provider),
                get_address(fast_withdrawal_contract),
                get_address(exchanger),
            )
            .with_amount(xtz_amount)
            .send()
        )
