from web3 import Web3
from eth_account.signers.local import LocalAccount
from scripts.helpers.etherlink.contract import (
    load_contract_type,
    originate_contract,
    EvmContractHelper,
)


class Erc20ProxyHelper(EvmContractHelper):
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

        ERC20Proxy = load_contract_type(web3, 'ERC20Proxy')
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

        return cls(contract=contract, web3=web3, account=account, address=address)
