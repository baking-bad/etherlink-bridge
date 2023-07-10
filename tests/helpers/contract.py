from pytezos.contract.interface import ContractInterface
from pytezos.client import PyTezosClient
from dataclasses import dataclass
from scripts.utility import (
    load_contract_from_address,
    load_contract_from_build,
    find_op_by_hash,
    get_address_from_op,
)


@dataclass
class ContractHelper:
    contract: ContractInterface
    storage: dict

    @classmethod
    def deploy_from_build(
        cls,
        name: str,
        client: PyTezosClient,
        storage: dict
    ) -> 'ContractHelper':
        """ Deploys contract from build directory by given name with given
            storage using given client """

        print(f'deploying {name}...')
        raw_contract = load_contract_from_build(name)
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
