from typing import Literal

from pydantic import BaseModel


class Bridge(BaseModel):
    l1_smart_rollup_address: str
    l1_rpc_url: str
    l2_rpc_url: str
    rollup_rpc_url: str
    l2_kernel_address: str
    l2_withdraw_precompile_address: str
    l2_native_withdraw_precompile_address: str
    rollup_commitment_period: int
    rollup_challenge_window: int
    l1_time_between_blocks: int


class Wallet(BaseModel):
    l1_private_key: str
    l1_public_key_hash: str
    l2_private_key: str
    l2_public_key: str
    l2_master_key: str


class Token(BaseModel):
    l1_asset_id: str
    l1_ticketer_address: str
    l1_ticket_helper_address: str
    l2_token_address: str
    ticket_hash: int
    ticket_content_hex: str


class Native(Token):
    l1_asset_id: str = Literal['xtz']
    l2_token_address: str = Literal['xtz']
