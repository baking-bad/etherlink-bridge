from dataclasses import dataclass
from os.path import join
from typing import Any, Tuple

from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup

from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.utility import get_build_dir, pack
from scripts.helpers.utility import originate_from_file


# TODO: consider moving to a separate file?
@dataclass
class Withdrawal:
    withdrawal_id: int
    withdrawal_amount: int
    timestamp: int
    base_withdrawer: Addressable
    payload: bytes
    l2_caller: bytes

    # TODO: consider renaming to as_storage_key?
    def as_tuple(self) -> Tuple[int, int, int, str, bytes, bytes]:
        return (
            self.withdrawal_id,
            self.withdrawal_amount,
            self.timestamp,
            get_address(self.base_withdrawer),
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


class FastWithdrawal(ContractHelper):
    @staticmethod
    def make_storage(
        exchanger: Addressable,
        smart_rollup: Addressable,
    ) -> dict[str, Any]:
        """Creates storage for the FastWithdrawal contract with empty
        withdrawals bigmap"""

        return {
            "exchanger": get_address(exchanger),
            "smart_rollup": get_address(smart_rollup),
            "withdrawals": {},
        }

    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
        exchanger: Addressable,
        smart_rollup: Addressable,
    ) -> OperationGroup:
        """Deploys FastWithdrawal for the specified exchanger and smart_rollup
        addresses"""

        storage = cls.make_storage(exchanger, smart_rollup)
        filename = join(get_build_dir(), "fast-withdrawal.tz")
        return originate_from_file(filename, client, storage)
