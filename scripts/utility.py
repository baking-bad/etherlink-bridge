# TODO: consider move this file to tests directory
from pytezos.client import PyTezosClient
from pytezos.contract.interface import ContractInterface
from pytezos.operation.group import OperationGroup
from os.path import dirname
from os.path import join


# Default address used as a placeholder in the contract storage
DEFAULT_ADDRESS = 'tz1burnburnburnburnburnburnburjAYjjX'


def pkh(client: PyTezosClient) -> str:
    return str(client.key.public_key_hash())


def find_op_by_hash(client: PyTezosClient, opg: OperationGroup) -> dict:
    """ Finds operation group by operation hash """

    op = client.shell.blocks[-10:].find_operation(opg.hash())
    return op  # type: ignore


def get_address_from_op(op: dict) -> str:
    """ Returns originated contract address from given operation dict """

    contents = op['contents']
    assert len(contents) == 1, 'multiple origination not supported'
    op_result: dict = contents[0]['metadata']['operation_result']
    contracts = op_result['originated_contracts']
    assert len(contracts) == 1, 'multiple origination not supported'
    originated_contract = contracts[0]
    assert type(originated_contract) is str
    return originated_contract


def make_filename_from_build_name(name: str) -> str:
    build_dir = join(dirname(__file__), '..', 'build')
    return join(build_dir, name + '.tz')


def load_contract_from_address(
    client: PyTezosClient,
    contract_address: str
) -> ContractInterface:
    """ Loads contract from given address using given client """

    contract = client.contract(contract_address)
    contract = contract.using(shell=client.shell, key=client.key)
    return contract
