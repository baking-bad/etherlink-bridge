from pytezos.contract.interface import ContractInterface
from pytezos.client import PyTezosClient
from dataclasses import dataclass
from scripts.utility import (
    load_contract_from_address,
    find_op_by_hash,
    get_address_from_op,
)
from typing import TypeVar, Type, Any


T = TypeVar('T', bound='ContractHelper')

@dataclass
class ContractHelper:
    contract: ContractInterface
    default_storage: Any
    client: PyTezosClient
    address: str

    # TODO: consider splitting this deploy to two methods:
    #       - first one will prepare origination operation
    #       - second one will create ContractHelper from opg
    #       (this will allow to call bake_block in tests between these two)
    #       (this also allows batch originations)
    @classmethod
    def deploy_from_file(
        cls: Type[T],
        filename: str,
        client: PyTezosClient,
        storage: Any
    ) -> T:
        """ Deploys contract from filename with given storage
            using given client """

        print(f'deploying contract from filename {filename}')
        raw_contract = ContractInterface.from_file(filename)
        contract = raw_contract.using(key=client.key, shell=client.shell)
        opg = contract.originate(initial_storage=storage).send()
        print(f'success: {opg.hash()}')

        client.wait(opg)
        op = find_op_by_hash(client, opg)
        address = get_address_from_op(op)
        print(f'addres: {address}')

        return cls(
            contract=load_contract_from_address(client, address),
            default_storage=storage,
            client=client,
            address=address,
        )

    # TODO: consider adding .using(**kwargs) method to ContracHelper that will
    #       return new ContractHelper with contract.using(**kwargs)
