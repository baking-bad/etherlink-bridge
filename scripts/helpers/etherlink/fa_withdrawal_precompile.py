from web3.types import TxReceipt
from scripts.helpers.etherlink.contract import EvmContractHelper


class FaWithdrawalPrecompileHelper(EvmContractHelper):
    def withdraw(
        self,
        ticket_owner: str,
        routing_info: bytes,
        # TODO: consider using BigNumber instead of int
        amount: int,
        ticketer: bytes,
        content: bytes,
    ) -> TxReceipt:
        """Withdraws tokens from L2 to L1"""

        transaction = self.contract.functions.withdraw(
            ticket_owner, routing_info, amount, ticketer, content
        ).build_transaction(
            {
                'from': self.account.address,
                # TODO: check if gas limit can be reduced
                'gas': 10_000_000,
                'gasPrice': self.web3.to_wei('1', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'chainId': self.web3.eth.chain_id,
            }
        )

        signed_txn = self.web3.eth.account.sign_transaction(
            transaction, self.account.key
        )
        txn_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_receipt
