from urllib.parse import urlparse, urlunparse, urlencode
import requests
from scripts.helpers.ticket import Ticket
from typing import Optional


def make_ticket_table_key(ticket: Ticket, owner_address: str) -> str:
    """Make a durable storage key for the given ticket and owner address."""

    kernel_address = '0000000000000000000000000000000000000000'
    address = owner_address.replace('0x', '').lower()
    # TODO: check if it is required to add leading zeroes:
    ticket_hash_hex = hex(ticket.hash()).replace('0x', '').lower()
    key = f'/evm/world_state/eth_accounts/{kernel_address}/ticket_table/{ticket_hash_hex}/{address}'
    return key


def get_durable_storage_value(rollup_node_url: str, key: str) -> Optional[str]:
    """Get a durable storage value from the given rollup node URL by given key."""

    parts = urlparse(rollup_node_url)
    parts = parts._replace(
        path='global/block/head/durable/wasm_2_0_0/value',
        query=urlencode(dict(key=key)),
    )
    url = urlunparse(parts)
    return requests.get(url).json()  # type: ignore


def get_tickets_count(rollup_node_url: str, ticket: Ticket, owner_address: str) -> int:
    """Get the number of tickets for the given ticket and owner address."""

    storage_value = get_durable_storage_value(
        rollup_node_url,
        make_ticket_table_key(ticket, owner_address),
    )
    if storage_value is None:
        return 0

    return int.from_bytes(bytes.fromhex(storage_value), 'little')
