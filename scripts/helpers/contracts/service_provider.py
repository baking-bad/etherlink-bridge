from os.path import join
from typing import Any

from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup

from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.utility import get_build_dir
from scripts.helpers.utility import originate_from_file


class ServiceProvider(ContractHelper):
    @staticmethod
    def make_storage(
        dummy_address: Addressable,
    ) -> dict[str, Any]:
        """Creates a dummy storage for ServiceProvider"""

        return {
            "fast_withdrawal_contract": dummy_address,
            "exchanger": dummy_address,
            "withdrawal_id": 0,
            "target": dummy_address,
            "timestamp": 0,
            "service_provider": dummy_address,
            "payload": bytes(0),
            "l2_caller": bytes(0),
            "full_amount": 0,
        }

    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
    ) -> OperationGroup:
        """Deploys ServiceProvider contract with a dummy storage"""

        storage = cls.make_storage(get_address(client))
        filename = join(get_build_dir(), "service-provider.tz")
        return originate_from_file(filename, client, storage)

    def payout_proxy(
        self,
        fast_withdrawal_contract: Addressable,
        exchanger: Addressable,
        withdrawal_id: int,
        target: Addressable,
        timestamp: int,
        service_provider: Addressable,
        payload: bytes,
        l2_caller: bytes,
        full_amount: int,
        xtz_amount: int = 0,
    ) -> OperationGroup:
        """Creates an operation with call to the payout_proxy entrypoint"""

        return (
            self.contract.payout_proxy(
                get_address(fast_withdrawal_contract),
                get_address(exchanger),
                withdrawal_id,
                get_address(target),
                timestamp,
                get_address(service_provider),
                payload,
                l2_caller,
                full_amount,
            )
            .with_amount(xtz_amount)
            .send()
        )
