import json
from os.path import dirname, join

from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import TxReceipt

# 0xff..02 FA bridge precompile (ABI shared at abi/fa_bridge.json).
# TODO: merge with FaWithdrawalPrecompileHelper — both wrap this precompile.
with open(join(dirname(__file__), 'abi', 'fa_bridge.json')) as _abi_file:
    _FA_BRIDGE_ABI = json.load(_abi_file)['abi']


class FaBridgeDepositClaimer:
    """Finds queued FA deposits and claims them on the FA bridge precompile."""

    def __init__(self, web3: Web3, account: LocalAccount, precompile_address: str):
        self.web3 = web3
        self.account = account
        self.contract = web3.eth.contract(
            address=Web3.to_checksum_address(precompile_address),
            abi=_FA_BRIDGE_ABI,
        )

    def find_queued_nonces(
        self,
        ticket_hash: int,
        erc20_proxy: str,
        receiver: str,
        block_window: int = 10_000,
        chunk: int = 100,
    ) -> list[int]:
        """Returns the nonces of `QueuedDeposit` events matching the given ticket,
        proxy and receiver, scanning the last `block_window` L2 blocks in `chunk`-
        sized windows (the node caps the getLogs block range)."""

        receiver_address = Web3.to_checksum_address(receiver)
        head = int(self.web3.eth.block_number)
        floor = max(head - block_window, 0)
        nonces: list[int] = []
        hi = head
        while hi > floor:
            lo = max(hi - chunk + 1, floor)
            events = self.contract.events.QueuedDeposit().get_logs(  # type: ignore[attr-defined]
                fromBlock=lo,
                toBlock=hi,
                argument_filters={
                    'ticketHash': ticket_hash,
                    'proxy': Web3.to_checksum_address(erc20_proxy),
                },
            )
            for event in events:
                args = event['args']
                if Web3.to_checksum_address(args['receiver']) == receiver_address:
                    nonces.append(int(args['nonce']))
            hi = lo - 1
        return nonces

    def claim(self, nonce: int) -> TxReceipt:
        """Claims a single queued deposit by its nonce, finalising the L2 mint."""

        transaction = self.contract.functions.claim(nonce).build_transaction(
            {
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'chainId': self.web3.eth.chain_id,
            }
        )
        signed = self.web3.eth.account.sign_transaction(transaction, self.account.key)
        tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
        return self.web3.eth.wait_for_transaction_receipt(tx_hash)
