from tests.base import BaseTestCase
from scripts.utility import pkh


class TicketerCommunicationTestCase(BaseTestCase):
    def test_wrap_and_send_ticket_using_proxy(self) -> None:
        # TODO: make a batch call with all operations
        self.fa2.allow(self.ticketer.address).send()
        self.bake_block()

        self.ticketer.deposit(self.fa2, 100).send()
        self.bake_block()
        assert self.fa2.get_balance(self.ticketer.address) == 100

        self.proxy.set({
            'data': pkh(self.manager),
            'receiver': self.locker.address,
        }).send()
        self.bake_block()

        # TODO: move this to utility:
        from pytezos.michelson.parse import michelson_to_micheline
        from pytezos.michelson.types.base import MichelsonType
        from typing import Any

        def to_micheline(type_expression: str) -> dict:
            return michelson_to_micheline(type_expression)  # type: ignore

        def to_michelson_type(object: Any, type_expression: str) -> MichelsonType:
            micheline_expression = to_micheline(type_expression)
            michelson_type = MichelsonType.match(micheline_expression)
            return michelson_type.from_python_object(object)

        def pack(object: Any, type_expression: str) -> bytes:
            return to_michelson_type(object, type_expression).pack()

        # TODO: move this token_info generation to Token & FA2 module
        token_info = {
            'contract_address': pack(self.fa2.address, 'address'),
            'token_id': pack(self.fa2.token_id, 'nat'),
            'token_type': pack("FA2", 'string'),
        }

        ticket_contents = {
            'token_id': 0,
            'token_info': pack(token_info, 'map %token_info string bytes')
        }
        ticket_type_expression = 'pair (nat %token_id) (bytes %token_info)'

        ticket_params = {
            'ticket_contents': to_michelson_type(
                ticket_contents,
                ticket_type_expression,
            ).to_micheline_value(),
            'ticket_ty': to_micheline(ticket_type_expression),
            'ticket_ticketer': self.ticketer.address,
            'ticket_amount': 25,
            'destination': self.proxy.address,
            'entrypoint': 'send_ticket'
        }

        assert len(self.locker.get_tickets()) == 0
        self.manager.transfer_ticket(**ticket_params).send()
        self.bake_block()

        # TODO: improve this check and make sure ticket payload and amount is correct
        assert len(self.locker.get_tickets()) == 1

        # TODO: release ticket
