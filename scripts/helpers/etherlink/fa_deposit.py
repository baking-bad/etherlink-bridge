import json
from collections.abc import Iterator
from os.path import dirname, join

from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import TxReceipt

# 0xff..02 FA bridge precompile (ABI shared at abi/fa_bridge.json).
# TODO: merge with FaWithdrawalPrecompileHelper — both wrap this precompile.
with open(join(dirname(__file__), 'abi', 'fa_bridge.json')) as _abi_file:
    _FA_BRIDGE_ABI = json.load(_abi_file)['abi']


class FaBridgeDepositClaimer:
    """Finds queued FA deposits by their `QueuedDeposit` nonce and claims them."""

    def __init__(self, web3: Web3, account: LocalAccount, precompile_address: str):
        self.web3 = web3
        self.account = account
        self.contract = web3.eth.contract(
            address=Web3.to_checksum_address(precompile_address),
            abi=_FA_BRIDGE_ABI,
        )

    def _iter_nonces(
        self,
        ticket_hash: int,
        erc20_proxy: str,
        receiver: str,
        chunk: int = 100,
        max_blocks: int = 2_000,
    ) -> Iterator[int]:
        """Yields matching nonces newest-first, scanning the L2 head backward in
        `chunk`-sized windows (the node caps the getLogs range). Lazy: the caller
        stops it once satisfied, so the common lookup is a single getLogs call."""

        receiver = Web3.to_checksum_address(receiver)
        proxy = Web3.to_checksum_address(erc20_proxy)
        hi = int(self.web3.eth.block_number)
        floor = max(hi - max_blocks, 0)
        while hi >= floor:
            lo = max(hi - chunk + 1, floor)
            events = self.contract.events.QueuedDeposit().get_logs(  # type: ignore[attr-defined]
                fromBlock=lo,
                toBlock=hi,
                argument_filters={'ticketHash': ticket_hash, 'proxy': proxy},
            )
            # get_logs returns ascending; reverse for newest-first within the chunk.
            for event in reversed(events):
                args = event['args']
                if Web3.to_checksum_address(args['receiver']) == receiver:
                    yield int(args['nonce'])
            hi = lo - 1

    def latest_queued_nonce(
        self, ticket_hash: int, erc20_proxy: str, receiver: str
    ) -> int:
        """The newest nonce for the token/receiver, or -1 if none."""

        return next(self._iter_nonces(ticket_hash, erc20_proxy, receiver), -1)

    def queued_nonces_since(
        self, ticket_hash: int, erc20_proxy: str, receiver: str, since_nonce: int
    ) -> list[int]:
        """Nonces greater than `since_nonce` (ascending); stops at the first one
        <= it, since nonces are monotonic."""

        fresh: list[int] = []
        for nonce in self._iter_nonces(ticket_hash, erc20_proxy, receiver):
            if nonce <= since_nonce:
                break
            fresh.append(nonce)
        return sorted(fresh)

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
