# TODO: consider splitting to multiple files (?)

from scripts.helpers.etherlink.contract import (
    EvmContractHelper,
    make_filename,
)
from web3.types import TxReceipt


class BulkWithdrawalHelper(EvmContractHelper):
    filename = make_filename('BulkWithdrawal')


class DepositTesterHelper(EvmContractHelper):
    filename = make_filename('DepositTester')


class TokenProxyTesterHelper(EvmContractHelper):
    filename = make_filename('TokenProxyTester')

    # TODO: consider simplify TokenProxyTester and remove this method
    def set_parameters(
        self,
        # TODO: make some of the parameters optional and if not provided check the current storage value?
        ticket_owner: str,
        withdrawal_precompile: str,
        routing_info: bytes,
        amount: int,
        ticketer: bytes,
        content: bytes,
        calls_count: int,
    ) -> TxReceipt:
        """Replaces TokenProxyHelper parameters with provided"""

        call = self.contract.functions.setParameters(
            ticket_owner,
            withdrawal_precompile,
            routing_info,
            amount,
            ticketer,
            content,
            calls_count,
        )

        # TODO: this build_transaction can be created inside self.legacy_send
        #       but for xtz withdrawal precompile call we need `value` to be provided too
        # TODO: consider refactoring `legacy_send`
        transaction = call.build_transaction(
            {
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'chainId': self.web3.eth.chain_id,
            }
        )

        return self.legacy_send(transaction)