import unittest
from tezos.tests.helpers.contracts.tokens import FA2
from tezos.tests.helpers.ticket_content import TicketContent
from unittest.mock import Mock


def split_by(string, by=64):
    return [
        string[n*by:(n+1)*by] for n in range(len(string) // by + 1)
    ]

class TestTicketContentGeneration(unittest.TestCase):
    def test_ticket_content_generation_for_empty_metadata(self) -> None:
        content = TicketContent(0, None)
        expected_content = '070700000306'
        assert content.to_bytes_hex() == expected_content
        self.assertDictEqual(
            content.to_micheline(),
            {'prim': 'Pair', 'args': [{'int': '0'}, {'prim': 'None'}]}
        )

    def test_ticket_content_generation_for_fa2_without_extra_metadata(self) -> None:
        mock_contract = Mock()
        mock_client = Mock()
        token_address = 'KT1LpdETWYvPWCQTR2FEW6jE6dVqJqxYjdeW'
        token = FA2(mock_contract, mock_client, token_address, 0)
        token_info_bytes = token.make_token_info_bytes()
        expected_token_info_hex = (
            '05020000006e07040100000010636f6e74726163745f616464726573730a0000'
            + '001c050a00000016018640607e2f2c3483ae9f15707d1823d4351742e0000704'
            + '0100000008746f6b656e5f69640a000000030500000704010000000a746f6b65'
            + '6e5f747970650a00000009050100000003464132'
        )
        assert token_info_bytes.hex() == expected_token_info_hex

        content = TicketContent(0, token_info_bytes)
        expected_content = (
            '0707000005090a0000007405020000006e07040100000010636f6e7472616374'
            + '5f616464726573730a0000001c050a00000016018640607e2f2c3483ae9f1570'
            + '7d1823d4351742e00007040100000008746f6b656e5f69640a00000003050000'
            + '0704010000000a746f6b656e5f747970650a00000009050100000003464132'
        )
        assert content.to_bytes_hex() == expected_content
