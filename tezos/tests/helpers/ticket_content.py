from tezos.tests.helpers.utility import to_michelson_type
from pytezos.michelson.types.base import MichelsonType
from dataclasses import dataclass
from tezos.tests.helpers.utility import to_micheline
from typing import (
    Optional,
    Any,
)


@dataclass
class TicketContent:
    token_id: int
    token_info: Optional[bytes]
    michelson_type = '(pair nat (option bytes))'

    @classmethod
    def from_micheline(cls, content: dict[str, Any]) -> 'TicketContent':
        """Converts ticket content to the tuple form"""
        token_id = int(content['args'][0]['int'])
        token_info = None
        has_token_info = content['args'][1]['prim'] == 'Some'
        if has_token_info:
            token_info = bytes.fromhex(content['args'][1]['args'][0]['bytes'])
        return cls(token_id=token_id, token_info=token_info)

    def to_micheline(self) -> dict[str, Any]:
        return to_michelson_type(  # type: ignore
            (self.token_id, self.token_info),
            self.michelson_type,
        ).to_micheline_value()

    def to_bytes_hex(self) -> str:
        """This function allows to make ticket payload bytes to be used in
        L2 Etherlink Bridge contracts"""

        michelson_type = MichelsonType.match(to_micheline(self.michelson_type))
        micheline_value = self.to_micheline()
        value = michelson_type.from_micheline_value(micheline_value)
        payload: str = value.forge('legacy_optimized').hex()
        return payload

    def to_tuple(self) -> tuple[int, Optional[bytes]]:
        return (self.token_id, self.token_info)
