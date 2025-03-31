from typing import Union, Type, TYPE_CHECKING
from pytezos.client import PyTezosClient
from eth_account.signers.local import LocalAccount
from scripts.helpers.etherlink import EvmContractHelper
from scripts.helpers.utility import pack

if TYPE_CHECKING:
    from scripts.helpers.contracts.contract import ContractHelper


# TODO: consider renaming to TezosAddressable?
Addressable = Union['ContractHelper', PyTezosClient, str]
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


def tezos_address_to_bytes(tezos_entity: Addressable) -> bytes:
    """Forges Tezos contract address (KT1, tz1, tz2, tz3) to bytes.
    Forged contract consists of binary suffix/prefix and body
    (blake2b hash digest)"""

    # packing address to bytes and taking the last 22 bytes:
    return pack(get_address(tezos_entity), 'address')[-22:]


def etherlink_address_to_bytes(etherlink_entity: EtherlinkAddressable) -> bytes:
    address = get_etherlink_address(etherlink_entity)
    return bytes.fromhex(address.replace('0x', ''))


# TODO: consider moving to separate module?
def make_deposit_routing_info(
    receiver: EtherlinkAddressable,
    # TODO: make router Optional
    router: EtherlinkAddressable,
) -> bytes:
    return etherlink_address_to_bytes(receiver) + etherlink_address_to_bytes(router)


def make_withdrawal_routing_info(
    receiver: Addressable,
    router: Addressable,
) -> bytes:
    return tezos_address_to_bytes(receiver) + tezos_address_to_bytes(router)
