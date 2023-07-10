from pytezos.contract.interface import ContractInterface
from pytezos.client import PyTezosClient
from dataclasses import dataclass
from scripts.utility import (
    load_contract_from_address,
    find_op_by_hash,
    get_address_from_op,
)


@dataclass
class ContractHelper:
    contract: ContractInterface
    storage: dict

    @classmethod
    def deploy_from_file(
        cls,
        filename: str,
        client: PyTezosClient,
        storage: dict
    ) -> 'ContractHelper':
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
            storage=storage,
        )
