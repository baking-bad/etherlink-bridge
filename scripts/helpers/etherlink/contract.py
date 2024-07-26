from web3.contract import Contract, ContractConstructor  # type: ignore
from web3 import Web3
from os.path import join, dirname
from eth_account.signers.local import LocalAccount
import json
from dataclasses import dataclass
from typing import Optional
from hexbytes import HexBytes
from typing import TypeVar, Type, Tuple, Any
from web3.types import TxReceipt, TxParams


def make_filename(contract_name: str) -> str:
    """Returns a path to the contract for a given contract name."""

    return join(
        dirname(__file__),
        '..',
        '..',
        '..',
        'etherlink',
        'build',
        f'{contract_name}.sol',
        f'{contract_name}.json',
    )


def load_contract_type(web3: Web3, filename: str) -> Type[Contract]:
    """Loads a Contract class from a given filename."""

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
    # TODO: consider remove these optional parameters:
    gas_limit: Optional[int] = None,
    gas_price: Optional[int] = None,
    nonce: Optional[int] = None,
) -> HexBytes:
    # TODO: estimate gas and request gas price
    # gas_limit = gas_limit or constructor.estimate_gas(transaction=transaction)
    # gas_price = gas_price or web3.eth.gas_price
    gas_limit = gas_limit or 30_000_000
    gas_price = gas_price or web3.to_wei('1', 'gwei')
    nonce = nonce or web3.eth.get_transaction_count(account.address)

    transaction_parameters = {
        'from': account.address,
        # TODO: consider remove:
        # 'gas': gas_limit,
        # 'gasPrice': gas_price,
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

    def legacy_send(self, params: TxParams) -> TxReceipt:
        signed_txn = self.web3.eth.account.sign_transaction(params, self.account.key)
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_receipt

    @classmethod
    def originate_from_file(
        cls: Type[T],
        web3: Web3,
        account: LocalAccount,
        filename: str,
        constructor_args: Tuple[Any, ...],
    ) -> T:
        """Deploys contract with given parameters"""

        Contract = load_contract_type(web3, filename)
        constructor = Contract.constructor(*constructor_args)

        tx_hash = originate_contract(
            web3=web3,
            account=account,
            constructor=constructor,
            # TODO: consider remove:
            # gas_limit=30_000_000,
            # gas_price=web3.to_wei('1', 'gwei'),
            # nonce=None,
        )
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        address = tx_receipt.contractAddress  # type: ignore
        contract = web3.eth.contract(address=address, abi=Contract.abi)

        return cls(contract=contract, web3=web3, account=account, address=address)
