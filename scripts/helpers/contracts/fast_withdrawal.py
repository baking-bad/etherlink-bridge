from dataclasses import dataclass, replace
from os.path import join
from typing import Any, Optional, Tuple, Union

from pytezos.client import PyTezosClient
from pytezos.contract.call import ContractCall
from pytezos.operation.group import OperationGroup

from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.metadata import Metadata
from scripts.helpers.utility import get_build_dir
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

    def override(self, **kwargs: Any) -> "Withdrawal":
        return replace(self, **kwargs)


@dataclass
class Claimed:
    provider: str

    def __init__(self, provider: Addressable):
        self.provider = get_address(provider)


@dataclass(frozen=True)
class Cemented:
    pass


@dataclass
class Status:
    value: Optional[Union[Claimed, Cemented]]

    def unwrap(self) -> Union[Claimed, Cemented]:
        if self.value is None:
            raise AssertionError("Expected a status but got None")
        return self.value

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> "Status":
        if data is None:
            return cls(value=None)
        if "claimed" in data:
            return cls(value=Claimed(provider=data["claimed"]))
        if "cemented" in data:
            return cls(value=Cemented())
        raise ValueError("Invalid status data: expected a claimed or cemented object.")


class FastWithdrawal(ContractHelper):
    @staticmethod
    def make_storage(
        xtz_ticketer: Addressable,
        smart_rollup: Addressable,
        expiration_seconds: int,
    ) -> dict[str, Any]:
        """Creates storage for the FastWithdrawal contract with empty
        withdrawals bigmap"""

        metadata = Metadata.make_default(
            name="Fast Withdrawal",
            description="Fast Withdrawal is a component of the Etherlink Bridge that allows service providers to make fast payouts for user withdrawals and receive funds from Etherlink after outbox message settlement.",
            # TODO: don't forget to update the version
            version='0.1.0',
        )

        return {
            "config": {
                "xtz_ticketer": get_address(xtz_ticketer),
                "smart_rollup": get_address(smart_rollup),
                "expiration_seconds": expiration_seconds,
            },
            "withdrawals": {},
            "metadata": metadata,
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

    def get_status_view(self, withdrawal: Withdrawal) -> Status:
        """Returns status for the specified withdrawal, if it exists,
        otherwise returns None"""

        status = self.contract.get_status(withdrawal.as_tuple()).run_view()  # type: ignore
        return Status.from_dict(status)

    def get_config_view(self) -> dict[str, Any]:
        """Returns FastWithdrawal contract configuration"""

        return self.contract.get_config().run_view()  # type: ignore
