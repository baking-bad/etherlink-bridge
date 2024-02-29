import unittest
from tezos.tests.helpers.contracts.tokens import FA2, FA12
from tezos.tests.helpers.ticket_content import TicketContent
from unittest.mock import Mock
from tezos.tests.helpers.utility import pack


class TestTicketContentGeneration(unittest.TestCase):
    def test_ticket_content_generation_for_empty_metadata(self) -> None:
        content = TicketContent(0, None)
        expected_content = '070700000306'
        assert content.to_bytes_hex() == expected_content
        self.assertDictEqual(
            content.to_micheline(),
            {'prim': 'Pair', 'args': [{'int': '0'}, {'prim': 'None'}]},
        )

    def test_ticket_content_generation_for_fa12_without_extra_metadata(self) -> None:
        mock_contract = Mock()
        mock_client = Mock()
        token_address = 'KT1LpdETWYvPWCQTR2FEW6jE6dVqJqxYjdeW'
        token = FA12(mock_contract, mock_client, token_address, 0)
        token_info_bytes = token.make_token_info_bytes()
        expected_token_info_hex = (
            '05020000005907040100000010636f6e74726163745f616464726573730a0000'
            + '001c050a00000016018640607e2f2c3483ae9f15707d1823d4351742e0000704'
            + '010000000a746f6b656e5f747970650a0000000b0501000000054641312e32'
        )
        assert token_info_bytes.hex() == expected_token_info_hex

        content = TicketContent(0, token_info_bytes)
        expected_content = (
            '0707000005090a0000005f05020000005907040100000010636f6e7472616374'
            + '5f616464726573730a0000001c050a00000016018640607e2f2c3483ae9f1570'
            + '7d1823d4351742e0000704010000000a746f6b656e5f747970650a0000000b05'
            + '01000000054641312e32'
        )
        assert content.to_bytes_hex() == expected_content

    def test_ticket_content_generation_for_fa2_without_extra_metadata(self) -> None:
        mock_contract = Mock()
        mock_client = Mock()
        token_address = 'KT195Eb8T524v5VJ99ZzH2wpnPfQ2wJfMi6h'
        token = FA2(mock_contract, mock_client, token_address, 42)
        token_info_bytes = token.make_token_info_bytes()
        expected_token_info_hex = (
            '05020000006e07040100000010636f6e74726163745f616464726573730a0000'
            + '001c050a00000016010562347c75e60f8ef9a15242d8accc705d8798a9000704'
            + '0100000008746f6b656e5f69640a0000000305002a0704010000000a746f6b65'
            + '6e5f747970650a00000009050100000003464132'
        )
        assert token_info_bytes.hex() == expected_token_info_hex

        content = TicketContent(0, token_info_bytes)
        expected_content = (
            '0707000005090a0000007405020000006e07040100000010636f6e7472616374'
            + '5f616464726573730a0000001c050a00000016010562347c75e60f8ef9a15242'
            + 'd8accc705d8798a90007040100000008746f6b656e5f69640a0000000305002a'
            + '0704010000000a746f6b656e5f747970650a00000009050100000003464132'
        )
        assert content.to_bytes_hex() == expected_content

    def test_ticket_content_generation_with_extra_metadata_added(self) -> None:
        mock_contract = Mock()
        mock_client = Mock()
        token_address = 'KT195Eb8T524v5VJ99ZzH2wpnPfQ2wJfMi6h'
        token = FA2(mock_contract, mock_client, token_address, 42)
        token_info_bytes = token.make_token_info_bytes(
            {
                'decimals': pack(3, 'nat'),
                'symbol': pack('TEST', 'string'),
                'name': pack('Test Token', 'string'),
            }
        )

        expected_token_info_hex = (
            '0502000000c107040100000010636f6e74726163745f616464726573730a0000'
            + '001c050a00000016010562347c75e60f8ef9a15242d8accc705d8798a9000704'
            + '0100000008646563696d616c730a00000003050003070401000000046e616d65'
            + '0a0000001005010000000a5465737420546f6b656e0704010000000673796d62'
            + '6f6c0a0000000a0501000000045445535407040100000008746f6b656e5f6964'
            + '0a0000000305002a0704010000000a746f6b656e5f747970650a000000090501'
            + '00000003464132'
        )
        assert token_info_bytes.hex() == expected_token_info_hex
