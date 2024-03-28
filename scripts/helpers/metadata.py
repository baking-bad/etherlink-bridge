import json
from typing import Any


def to_hex(string: str) -> str:
    """Converts given string to bytes and then hex"""
    return string.encode().hex()


class Metadata:
    """Helper to create metadata for the contracts"""

    template = {
        'version': '0.4.1',
        'name': 'Etherlink Bridge',
        'description': 'The Etherlink Bridge consists of contracts designed for communication between Tezos and Etherlink rollup.',
        'interfaces': ['TZIP-016'],
        'license': {'name': 'MIT'},
        'homepage': 'https://github.com/baking-bad/etherlink-bridge',
    }

    @staticmethod
    def make(**kwargs: Any) -> dict:
        """Creates metadata from provided kwargs dict"""

        metadata_json = json.dumps(kwargs)
        return {
            '': to_hex('tezos-storage:contents'),
            'contents': to_hex(metadata_json),
        }

    @classmethod
    def make_default(cls, **kwargs: str) -> dict:
        """Creates metadata using default metadata as a template"""

        metadata = cls.template.copy()
        metadata.update(kwargs)
        return Metadata.make(**metadata)
