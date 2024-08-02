from web3.types import TxReceipt
from scripts.helpers.etherlink.contract import (
    EvmContractHelper,
    make_filename,
)


class FaWithdrawalPrecompileHelper(EvmContractHelper):
    # TODO: consider adding FaWithdrawalPrecompile ABI to the repo
    filename = make_filename('KernelMock')

    def withdraw(
        self,
        ticket_owner: str,
        routing_info: bytes,
        # TODO: consider using BigNumber instead of int
        amount: int,
        ticketer: bytes,
        content: bytes,
    ) -> TxReceipt:
        """Calls FA withdrawal precompile which allows to withdraw tokens from L2 to L1"""

        call = self.contract.functions.withdraw(
            ticket_owner, routing_info, amount, ticketer, content
        )

        transaction = call.build_transaction(
            {
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'chainId': self.web3.eth.chain_id,
            }
        )

        return self.legacy_send(transaction)
