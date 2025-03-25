from dataclasses import dataclass
from os.path import join
from typing import Any, Optional, Tuple

from pytezos.client import PyTezosClient
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup

from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.utility import get_build_dir, pack
from scripts.helpers.utility import originate_from_file
from scripts.helpers.ticket_content import TicketContent


# TODO: consider moving to a separate file?
@dataclass
class Withdrawal:
    withdrawal_id: int
    full_amount: int
    ticketer: Addressable
    content: TicketContent
    timestamp: int
    base_withdrawer: Addressable
    payload: bytes
    l2_caller: bytes

    # TODO: consider renaming to as_storage_key? (or maybe `to_tuple` as in TicketContent)
    def as_tuple(
        self,
    ) -> Tuple[int, int, str, Tuple[int, Optional[bytes]], int, str, bytes, bytes]:
        return (
            self.withdrawal_id,
            self.full_amount,
            get_address(self.ticketer),
            self.content.to_tuple(),
            self.timestamp,
            get_address(self.base_withdrawer),
            self.payload,
            self.l2_caller,
        )

    @classmethod
    def default_with(
        cls,
        withdrawal_id: int = 0,
        full_amount: int = 1_000_000,
        ticketer: Addressable = "tz1KqTpEZ7Yob7QbPE4Hy4Wo8fHG8LhKxZSx",
        content: TicketContent = TicketContent(0, None),
        base_withdrawer: Addressable = "tz1KqTpEZ7Yob7QbPE4Hy4Wo8fHG8LhKxZSx",
        timestamp: int = 0,
        payload: bytes = pack(1_000_000, 'nat'),
        l2_caller: bytes = bytes(20),
    ) -> 'Withdrawal':
        """Creates a default Withdrawal object filled with default values"""

        return cls(
            withdrawal_id=withdrawal_id,
            full_amount=full_amount,
            ticketer=ticketer,
            content=content,
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
        xtz_ticketer: Addressable,
        smart_rollup: Addressable,
        expiration_seconds: int,
    ) -> dict[str, Any]:
        """Creates storage for the FastWithdrawal contract with empty
        withdrawals bigmap"""

        return {
            "xtz_ticketer": get_address(xtz_ticketer),
            "smart_rollup": get_address(smart_rollup),
            "expiration_seconds": expiration_seconds,
            "withdrawals": {},
        }

    @classmethod
    def originate(
        cls,
        client: PyTezosClient,
        xtz_ticketer: Addressable,
        smart_rollup: Addressable,
        expiration_seconds: int,
    ) -> OperationGroup:
        """Deploys FastWithdrawal for the specified xtz_ticketer and smart_rollup
        addresses"""

        storage = cls.make_storage(xtz_ticketer, smart_rollup, expiration_seconds)
        filename = join(get_build_dir(), "fast-withdrawal.tz")
        return originate_from_file(filename, client, storage)

    def payout_withdrawal(
        self,
        withdrawal: Withdrawal,
        service_provider: Addressable,
        xtz_amount: int = 0,
    ) -> ContractCall:
        """Creates an operation with call to the payout_withdrawal entrypoint"""

        return self.contract.payout_withdrawal(
            withdrawal.as_tuple(),
            get_address(service_provider),
        ).with_amount(xtz_amount)
