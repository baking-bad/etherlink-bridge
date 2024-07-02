from pydantic import BaseModel

from scripts.bootstrap.const import DEFAULT_TOKEN_ID
from scripts.helpers.contracts import Ticketer


class TicketerParamsDTO(BaseModel):
    address_bytes_hex: str
    content_bytes_hex: str

class TicketerDTO(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    ticketer: Ticketer
    ticketer_params: TicketerParamsDTO
    ticket_hash: int

class TokenMetadataDTO(BaseModel):
    name: str
    symbol: str
    decimals: int = DEFAULT_TOKEN_ID

class TokenInfoDTO(BaseModel):
    metadata: TokenMetadataDTO
    standard: str
    supply: int

class UserInputDTO(BaseModel):
    is_mainnet: bool
    smart_rollup_address: str
    l1_private_key: str
    l2_private_key: str
    l1_rpc_url: str
    l2_rpc_url: str
    l1_testrunner_account: str
    use_test_prefix: bool
