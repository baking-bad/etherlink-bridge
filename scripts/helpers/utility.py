from pytezos.client import PyTezosClient
from pytezos import pytezos
from pytezos.contract.interface import ContractInterface
from pytezos.operation.group import OperationGroup
from os.path import dirname
from os.path import join
from pytezos.michelson.parse import michelson_to_micheline
from pytezos.michelson.types.base import MichelsonType
from typing import Any
from web3 import Web3
from eth_account.signers.local import LocalAccount
import click


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
    assert isinstance(originated_contract, str)
    return originated_contract


def get_build_dir() -> str:
    """Returns path to the build directory"""

    return join(dirname(__file__), '..', '..', 'tezos', 'build')


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
    """Converts address string to bytes"""  # fixme: REALLY?

    # packing address to bytes and taking the last 22 bytes:
    return pack(address, 'address')[-22:].hex()


def originate_from_file(
    filename: str, client: PyTezosClient, storage: Any
) -> OperationGroup:
    """Deploys contract from filename with given storage
    using given client and returns OperationGroup"""

    raw_contract = ContractInterface.from_file(filename)
    contract = raw_contract.using(key=client.key, shell=client.shell)
    return contract.originate(initial_storage=storage)


def get_tezos_client(shell: str, key: str) -> PyTezosClient:
    """Returns PyTezosClient using given shell and key"""

    client: PyTezosClient = pytezos.using(shell=shell, key=key)
    # TODO: validate balance, validate that account revealed (reuse logic from bootstrap?)

    return client


def get_etherlink_web3(shell: str) -> Web3:
    """Returns Web3 instance using given shell"""

    web3 = Web3(Web3.HTTPProvider(shell))
    if not web3.is_connected():
        raise Exception(f'Failed to connect to Etherlink node: {shell}')
    # TODO: validate balance (reuse logic from bootstrap?)

    return web3


def get_etherlink_account(web3: Web3, private_key: str) -> LocalAccount:
    """Returns LocalAccount using given web3 and private key"""

    account: LocalAccount = web3.eth.account.from_key(private_key)
    # TODO: validate balance

    return account


def accent(msg: str) -> str:
    return click.style(msg, fg='bright_cyan')


def wrap(msg: str, symbol: str = '`') -> str:
    return '`' + msg + '`'


def echo_variable(prefix: str, name: str, value: str) -> None:
    click.echo(prefix + name + ': ' + wrap(accent(value)))
