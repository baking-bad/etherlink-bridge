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

        transaction = self._tx_params()
        transaction['value'] = self.web3.to_wei(wei_amount, 'wei')
        call = self.contract.functions.withdraw_base58(receiver)
        return self.legacy_send(call.build_transaction(transaction))
