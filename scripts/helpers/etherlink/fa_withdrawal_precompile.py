from collections.abc import Iterator
from os.path import dirname, join

from web3 import Web3
from web3.types import TxReceipt

from scripts.helpers.etherlink.contract import EvmContractHelper


class FaWithdrawalPrecompileHelper(EvmContractHelper):
    """Wraps the FA bridge precompile (0xff..02): the `withdraw` entrypoint (L2->L1)
    and the deposit-claim side. The new kernel queues FA deposits; the L2 mint
    happens only once the deposit's `QueuedDeposit` nonce is claimed. That nonce
    surfaces only in the event (indexed by `ticketHash` + `proxy`); we match
    `receiver` and take the newest.
    """

    filename = join(dirname(__file__), 'abi', 'fa_bridge.json')

    def withdraw(
        self,
        ticket_owner: str,
        routing_info: bytes,
        # TODO: consider using BigNumber instead of int
        amount: int,
        ticketer: bytes,
        content: bytes,
    ) -> TxReceipt:
        """Withdraws a wrapped FA token (ERC20) from L2 back to L1."""

        call = self.contract.functions.withdraw(
            ticket_owner, routing_info, amount, ticketer, content
        )
        return self.legacy_send(call.build_transaction(self._tx_params()))

    def claim(self, nonce: int) -> TxReceipt:
        """Claims a single queued deposit by its nonce, finalising the L2 mint."""

        call = self.contract.functions.claim(nonce)
        return self.legacy_send(call.build_transaction(self._tx_params()))

    def latest_queued_nonce(
        self, ticket_hash: int, erc20_proxy: str, receiver: str
    ) -> int:
        """The newest queued-deposit nonce for the token/receiver, or -1 if none."""

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
