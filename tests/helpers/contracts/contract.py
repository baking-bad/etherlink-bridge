from pytezos.contract.interface import ContractInterface
from pytezos.client import PyTezosClient
from pytezos.operation.group import OperationGroup
from dataclasses import dataclass
from tests.helpers.utility import (
    load_contract_from_address,
    find_op_by_hash,
    get_address_from_op,
)
from typing import TypeVar, Type, Any


T = TypeVar('T', bound='ContractHelper')

@dataclass
class ContractHelper:
    contract: ContractInterface
    client: PyTezosClient
    address: str
    default_storage: Any = None

    @classmethod
    def originate_from_file(
        cls,
        filename: str,
        client: PyTezosClient,
        storage: Any
    ) -> OperationGroup:
        """ Deploys contract from filename with given storage
            using given client """

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
        """ Creates ContractHelper from given operation group
            with given client """

        op = find_op_by_hash(client, opg)
        address = get_address_from_op(op)
        print(f'found contract addres: {address}')

        return cls(
            contract=load_contract_from_address(client, address),
            client=client,
            address=address,
        )

    # TODO: consider adding .using(**kwargs) method to ContracHelper that will
    #       return new ContractHelper with contract.using(**kwargs) and
    #       updated client
