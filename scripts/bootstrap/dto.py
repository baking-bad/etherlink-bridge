from typing import Any

from pydantic import BaseModel

from scripts.helpers.contracts import Ticketer


class TicketerDTO(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    metadata: dict[str, Any]
    ticketer: Ticketer
    ticketer_params: dict[str, str]
    ticket_hash: int


class UserInputDTO(BaseModel):
    is_mainnet: bool
    smart_rollup_address: str
    l1_private_key: str
    l2_private_key: str
    l1_rpc_url: str
    l2_rpc_url: str
    l1_testrunner_account: str
    use_test_prefix: bool
