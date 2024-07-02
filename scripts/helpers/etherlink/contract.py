from web3.contract import Contract, ContractConstructor  # type: ignore
from web3 import Web3
from os.path import join, dirname
from eth_account.signers.local import LocalAccount
import json
from dataclasses import dataclass
from typing import Optional
from hexbytes import HexBytes
from typing import TypeVar, Type


def load_contract_type(web3: Web3, contract_name: str) -> Type[Contract]:
    """Returns a Contract class for a given contract name."""

    filename = join(
        dirname(__file__),
        '..',
        '..',
        '..',
        'etherlink',
        'build',
        f'{contract_name}.sol',
        f'{contract_name}.json',
    )

    with open(filename) as contract_json:
        contract_data = json.load(contract_json)

    return web3.eth.contract(
        abi=contract_data['abi'],
        bytecode=contract_data['bytecode']['object'],
    )


def originate_contract(
    web3: Web3,
    account: LocalAccount,
    constructor: ContractConstructor,
    gas_limit: Optional[int],
    gas_price: Optional[int],
    nonce: Optional[int],
) -> HexBytes:
    # TODO: estimate gas and request gas price
    # gas_limit = gas_limit or constructor.estimate_gas(transaction=transaction)
    # gas_price = gas_price or web3.eth.gas_price
    gas_limit = gas_limit or 30_000_000
    gas_price = gas_price or web3.to_wei('1', 'gwei')
    nonce = nonce or web3.eth.get_transaction_count(account.address)

    transaction_parameters = {
        'from': account.address,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'nonce': nonce,
    }
    transaction = constructor.build_transaction(transaction_parameters)

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=account.key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return tx_hash


T = TypeVar('T', bound='EvmContractHelper')


@dataclass
class EvmContractHelper:
    contract: Contract
    web3: Web3
    account: LocalAccount
    address: str

    @classmethod
    def from_address(
        cls: Type[T],
        contract_type: Type[Contract],
        web3: Web3,
        account: LocalAccount,
        address: str,
    ) -> T:
        # TODO: check if this OK to ignore type
        contract = web3.eth.contract(address=address, abi=contract_type.abi)  # type: ignore
        return cls(contract=contract, web3=web3, account=account, address=address)
