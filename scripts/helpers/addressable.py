from typing import Union
from scripts.helpers.contracts.contract import ContractHelper
from pytezos.client import PyTezosClient
from eth_account.signers.local import LocalAccount
from scripts.helpers.etherlink import EvmContractHelper


# TODO: consider renaming to TezosAddressable?
Addressable = Union[ContractHelper, PyTezosClient, str]
EtherlinkAddressable = Union[LocalAccount, EvmContractHelper, str]


# TODO: consider renaming to get_tezos_address?
def get_address(client_or_contract: Addressable) -> str:
    if isinstance(client_or_contract, ContractHelper):
        return client_or_contract.address
    if isinstance(client_or_contract, PyTezosClient):
        return client_or_contract.key.public_key_hash()
    if isinstance(client_or_contract, str):
        return client_or_contract
    raise ValueError(f'Unsupported type: {type(client_or_contract)}')


def get_etherlink_address(client_or_contract: EtherlinkAddressable) -> str:
    if isinstance(client_or_contract, LocalAccount):
        return str(client_or_contract.address)
    if isinstance(client_or_contract, EvmContractHelper):
        return client_or_contract.address
    if isinstance(client_or_contract, str):
        return client_or_contract
    raise ValueError(f'Unsupported type: {type(client_or_contract)}')
