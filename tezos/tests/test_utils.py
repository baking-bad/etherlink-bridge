import unittest
from scripts.helpers.contracts.tokens.fa12 import CtezToken
from scripts.helpers.contracts.tokens.fa2 import FxhashToken
from scripts.helpers.ticket_content import TicketContent
from unittest.mock import Mock


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
        token = CtezToken(mock_contract, mock_client, token_address, 0)
        token_info_bytes = token.make_token_info_bytes()
        expected_token_info_hex = (
            '05020000005b07040100000010636f6e74726163745f616464726573730a0000'
            + '00244b54314c7064455457597650574351545232464557366a45366456714a71'
            + '78596a6465570704010000000a746f6b656e5f747970650a000000054641312e'
            + '32'
        )
        assert token_info_bytes.hex() == expected_token_info_hex

        content = TicketContent(0, token_info_bytes)
        expected_content = (
            '0707000005090a0000006105020000005b07040100000010636f6e7472616374'
            + '5f616464726573730a000000244b54314c706445545759765057435154523246'
            + '4557366a45366456714a7178596a6465570704010000000a746f6b656e5f7479'
            + '70650a000000054641312e32'
        )
        assert content.to_bytes_hex() == expected_content

    def test_ticket_content_generation_for_fa2_without_extra_metadata(self) -> None:
        mock_contract = Mock()
        mock_client = Mock()
        token_address = 'KT195Eb8T524v5VJ99ZzH2wpnPfQ2wJfMi6h'
        token = FxhashToken(mock_contract, mock_client, token_address, 42)
        token_info_bytes = token.make_token_info_bytes()
        expected_token_info_hex = (
            '05020000006f07040100000010636f6e74726163745f616464726573730a0000'
            + '00244b54313935456238543532347635564a39395a7a483277706e5066513277'
            + '4a664d69366807040100000008746f6b656e5f69640a00000002343207040100'
            + '00000a746f6b656e5f747970650a00000003464132'
        )
        assert token_info_bytes.hex() == expected_token_info_hex

        content = TicketContent(0, token_info_bytes)
        expected_content = (
            '0707000005090a0000007505020000006f07040100000010636f6e7472616374'
            + '5f616464726573730a000000244b54313935456238543532347635564a39395a'
            + '7a483277706e50665132774a664d69366807040100000008746f6b656e5f6964'
            + '0a0000000234320704010000000a746f6b656e5f747970650a00000003464132'
        )
        assert content.to_bytes_hex() == expected_content

    def test_ticket_content_generation_with_extra_metadata_added(self) -> None:
        mock_contract = Mock()
        mock_client = Mock()
        token_address = 'KT195Eb8T524v5VJ99ZzH2wpnPfQ2wJfMi6h'
        token = FxhashToken(mock_contract, mock_client, token_address, 42)
        token_info_bytes = token.make_token_info_bytes(
            {
                'decimals': '3',
                'symbol': 'TEST',
                'name': 'Test Token',
            }
        )

        expected_token_info_hex = (
            '0502000000b407040100000010636f6e74726163745f616464726573730a0000'
            + '00244b54313935456238543532347635564a39395a7a483277706e5066513277'
            + '4a664d69366807040100000008646563696d616c730a00000001330704010000'
            + '00046e616d650a0000000a5465737420546f6b656e0704010000000673796d62'
            + '6f6c0a000000045445535407040100000008746f6b656e5f69640a0000000234'
            + '320704010000000a746f6b656e5f747970650a00000003464132'
        )
        assert token_info_bytes.hex() == expected_token_info_hex
