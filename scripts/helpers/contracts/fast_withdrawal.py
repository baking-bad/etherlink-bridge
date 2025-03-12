from os.path import join
from typing import Any

from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup

from scripts.helpers.addressable import Addressable, get_address
from scripts.helpers.contracts.contract import ContractHelper
from scripts.helpers.utility import get_build_dir
from scripts.helpers.utility import originate_from_file


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
