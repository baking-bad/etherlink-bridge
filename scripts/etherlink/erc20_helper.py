# TODO: consider moving to scripts/helpers/etherlink ?
from web3.contract import Contract, ContractConstructor  # type: ignore
from web3 import Web3
from os.path import join, dirname
from eth_account.signers.local import LocalAccount
import json
from dataclasses import dataclass
from typing import Optional
from hexbytes import HexBytes


def load_contract(web3: Web3, contract_name: str) -> type[Contract]:
    """Returns path to the Etherlink contract by its name"""

    filename = join(
        dirname(__file__),
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


@dataclass
class Erc20ProxyHelper:
    contract: Contract
    web3: Web3
    address: str

    @classmethod
    def originate(
        cls,
        web3: Web3,
        account: LocalAccount,
        ticketer: bytes,
        content: bytes,
        kernel: str,
        name: str,
        symbol: str,
        decimals: int,
    ) -> 'Erc20ProxyHelper':
        """Deploys ERC20 Proxy contract with given parameters"""

        ERC20Proxy = load_contract(web3, 'ERC20Proxy')
        constructor = ERC20Proxy.constructor(
            ticketer, content, kernel, name, symbol, decimals
        )

        tx_hash = originate_contract(
            web3=web3,
            account=account,
            constructor=constructor,
            gas_limit=30_000_000,
            gas_price=web3.to_wei('1', 'gwei'),
            nonce=None,
        )
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        address = tx_receipt.contractAddress  # type: ignore
        contract = web3.eth.contract(address=address, abi=ERC20Proxy.abi)

        return cls(contract=contract, web3=web3, address=address)
