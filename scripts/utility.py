from scripts.contracts import Contract
from pytezos.client import PyTezosClient
from pytezos.contract.interface import ContractInterface
from pytezos.operation.group import OperationGroup
from typing import Any


def pkh(client: PyTezosClient) -> str:
    return str(client.key.public_key_hash())


# TODO: use some number library for amount?
def generate_ticket_params(ticketer: str, amount: int, destination: str) -> dict:
    # TODO: need to find a way to encode ticket contents
    return {
        'ticket_contents': {"bytes": "TODO:"},
        'ticket_ty': {"prim": "bytes"},
        'ticket_ticketer': ticketer,
        'ticket_amount': amount,
        'destination': destination,
        'entrypoint': 'send'
    }


def load_contract(client: PyTezosClient, contract_address: str) -> ContractInterface:
    """Load originated contract from blockchain"""

    contract = client.contract(contract_address)
    contract = contract.using(shell=client.shell, key=client.key)
    return contract


def find_op_by_hash(client: PyTezosClient, opg: OperationGroup) -> dict:
    """ Finds operation group by operation hash """

    op = client.shell.blocks[-10:].find_operation(opg.hash())
    return dict(op)


def get_address_from_op(op: dict) -> str:
    """ Returns originated contract address from given operation dict """

    contents = op['contents']
    assert len(contents) == 1, 'multiple origination not supported'
    op_result: dict = contents[0]['metadata']['operation_result']
    return str(op_result['originated_contracts'][0])


def load_contract_from_opg(
    client: PyTezosClient,
    opg: OperationGroup
) -> ContractInterface:
    """Returns contract that was originated with within some operation group """

    op = find_op_by_hash(client, opg)
    address = get_address_from_op(op)
    return load_contract(client, address)


def deploy_contract_with_storage(
    client: PyTezosClient,
    contract: Contract,
    storage: Any
) -> str:
    """ Deploys contract with given storage and returns address """

    print(f'deploying {contract.name}...')
    treasure = ContractInterface.from_file(contract.filename)
    treasure = treasure.using(key=client.key, shell=client.shell)
    opg = treasure.originate(initial_storage=storage).send()
    print(f'success: {opg.hash()}')

    # TODO: would this work inside test environment or should bake_block be called?
    client.wait(opg)
    op = find_op_by_hash(client, opg)
    address = get_address_from_op(op)
    print(f'addres: {address}')
    return address
