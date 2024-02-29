import unittest
from tezos.tests.helpers.contracts.tokens import FA2
from unittest.mock import Mock


TOKEN_ADDRESS = 'KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton'


class TestTicketContentGeneration(unittest.TestCase):
    def test_ticket_content_generation_for_empty_metadata(self) -> None:
        mock_contract = Mock()
        mock_client = Mock()
        token = FA2(mock_contract, mock_client, TOKEN_ADDRESS, 0)
        token_info_hex = token.make_token_info_bytes().hex()
        expected_token_info_hex = (
            '05020000006e07040100000010636f6e74726163745f616464726573730a0000'
            + '001c050a0000001601b752c7f3de31759bce246416a6823e86b9756c6c000704'
            + '0100000008746f6b656e5f69640a000000030500000704010000000a746f6b65'
            + '6e5f747970650a00000009050100000003464132'
        )

        assert token_info_hex == expected_token_info_hex
