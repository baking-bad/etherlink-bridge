from pytezos.client import PyTezosClient
from pytezos.contract.interface import ContractInterface
from pytezos.operation.group import OperationGroup
from pytezos.crypto.encoding import base58_decode
from os.path import dirname
from os.path import join
from pytezos.michelson.parse import michelson_to_micheline
from pytezos.michelson.types.base import MichelsonType
from typing import Any


# Default address used as a placeholder in the contract storage
DEFAULT_ADDRESS = 'tz1burnburnburnburnburnburnburjAYjjX'


def pkh(client: PyTezosClient) -> str:
    """Returns public key hash of given client"""

    return str(client.key.public_key_hash())


def find_op_by_hash(client: PyTezosClient, opg: OperationGroup) -> dict:
    """Finds operation group by operation hash"""

    op = client.shell.blocks[-10:].find_operation(opg.hash())
    return op  # type: ignore


def get_address_from_op(op: dict) -> str:
    """Returns originated contract address from given operation dict"""

    contents = op['contents']
    assert len(contents) == 1, 'multiple origination not supported'
    op_result: dict = contents[0]['metadata']['operation_result']
    contracts = op_result['originated_contracts']
    assert len(contracts) == 1, 'multiple origination not supported'
    originated_contract = contracts[0]
    assert type(originated_contract) is str
    return originated_contract


def get_build_dir() -> str:
    """Returns path to the build directory"""

    return join(dirname(__file__), '..', '..', 'build')


def get_tokens_dir() -> str:
    """Returns path to the tokens directory"""

    return join(dirname(__file__), '..', 'tokens')


def load_contract_from_address(
    client: PyTezosClient, contract_address: str
) -> ContractInterface:
    """Loads contract from given address using given client"""

    contract = client.contract(contract_address)
    contract = contract.using(shell=client.shell, key=client.key)
    return contract


def to_micheline(type_expression: str) -> dict:
    """Converts Michelson type expression string to Micheline expression
    (reusing pytezos.michelson.parse.michelson_to_micheline) with
    type checking
    """

    return michelson_to_micheline(type_expression)  # type: ignore


def to_michelson_type(object: Any, type_expression: str) -> MichelsonType:
    """Converts Python object to Michelson type using given type expression"""

    micheline_expression = to_micheline(type_expression)
    michelson_type = MichelsonType.match(micheline_expression)
    return michelson_type.from_python_object(object)


def pack(object: Any, type_expression: str) -> bytes:
    """Packs Python object to bytes using given type expression"""

    return to_michelson_type(object, type_expression).pack()


def make_address_bytes(address: str) -> str:
    """Converts address string to bytes"""

    # packing address to bytes and taking the last 22 bytes:
    return pack(address, 'address')[-22:].hex()
