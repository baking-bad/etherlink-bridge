from pytezos.contract.interface import ContractInterface
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from dataclasses import dataclass, replace
from tests.helpers.utility import (
    load_contract_from_address,
    find_op_by_hash,
    get_address_from_op,
)
from typing import TypeVar, Type, Any
from abc import ABC, abstractmethod


T = TypeVar('T', bound='ContractHelper')


@dataclass
class ContractHelper(ABC):
    contract: ContractInterface
    client: PyTezosClient
    address: str
    default_storage: Any = None

    @classmethod
    def originate_from_file(
        cls, filename: str, client: PyTezosClient, storage: Any
    ) -> OperationGroup:
        """Deploys contract from filename with given storage
        using given client"""

        print(f'deploying contract from filename {filename}')
        raw_contract = ContractInterface.from_file(filename)
        contract = raw_contract.using(key=client.key, shell=client.shell)
        return contract.originate(initial_storage=storage)

    @classmethod
    def create_from_opg(
        cls: Type[T],
        client: PyTezosClient,
        opg: OperationGroup,
    ) -> T:
        """Creates ContractHelper from given operation group
        with given client"""

        op = find_op_by_hash(client, opg)
        address = get_address_from_op(op)
        print(f'found contract addres: {address}')

        return cls(
            contract=load_contract_from_address(client, address),
            client=client,
            address=address,
        )

    def using(self: T, client: PyTezosClient) -> T:
        """Returns new ContractHelper with updated client"""

        return replace(
            self,
            client=client,
            contract=client.contract(self.contract.address),
        )

    @classmethod
    def create_from_address(
        cls: Type[T],
        client: PyTezosClient,
        address: str,
    ) -> T:
        """Loads contract from given address using given client"""

        return cls(
            contract=client.contract(address),
            client=client,
            address=address,
        )
