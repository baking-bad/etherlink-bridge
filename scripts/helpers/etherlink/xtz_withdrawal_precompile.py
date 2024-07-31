from web3.types import TxReceipt
from scripts.helpers.etherlink.contract import (
    EvmContractHelper,
    make_filename,
)


class XtzWithdrawalPrecompileHelper(EvmContractHelper):
    # TODO: consider adding XtzWithdrawalPrecompile ABI to the repo
    filename = make_filename('KernelMock')

    def withdraw(
        self,
        receiver: str,
        # TODO: consider using BigNumber instead of int
        wei_amount: int,
    ) -> TxReceipt:
        """Calls XTZ withdrawal precompile which allows to withdraw XTZ from L2 to L1"""

        call = self.contract.functions.withdraw_base58(receiver)
        transaction = call.build_transaction(
            {
                'from': self.account.address,
                'value': self.web3.to_wei(wei_amount, 'wei'),
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'chainId': self.web3.eth.chain_id,
            }
        )

        txn_receipt = self.legacy_send(transaction)
        return txn_receipt
