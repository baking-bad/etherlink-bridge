"""EVM alias of a Tezos address.

On Tezos X every Michelson address (tz*/KT1) shadows an EVM account — its
*alias* — at `keccak256(utf8(b58_string))[:20]`. Depositing to the alias on the
L2 EVM side credits the native Michelson account (once the alias is initialised).
"""

from web3 import Web3


def compute_alias(tz_address: str) -> str:
    """The checksum-cased EVM alias of a Tezos address (tz*/KT1)."""

    return Web3.to_checksum_address(Web3.keccak(text=tz_address)[:20])


def alias_bytes(tz_address: str) -> bytes:
    """The 20-byte EVM alias of a Tezos address (raw, for deposit routing)."""

    return bytes(Web3.keccak(text=tz_address)[:20])
