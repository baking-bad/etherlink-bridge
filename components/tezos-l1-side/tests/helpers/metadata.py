import json


DEFAULT_METADATA = {
    'version': '0.2.0',
    'name': 'Etherlink Bridge',
    'description': 'The Etherlink Bridge consists of contracts designed for communication between Tezos and Etherlink rollup.',
    'interfaces': [
        'TZIP-016'
    ],
    'license': {
        'name': 'MIT'
    },
    'homepage': 'https://github.com/baking-bad/etherlink-bridge'
}


def to_hex(string: str) -> str:
    """Converts given string to bytes and then hex"""
    return string.encode().hex()


def make_metadata(**kwargs: str) -> dict:
    """Creates metadata for the contract"""
    metadata = DEFAULT_METADATA.copy()
    metadata.update(kwargs)
    metadata_json = json.dumps(metadata)

    return {
        '': to_hex('tezos-storage:contents'),
        'contents': to_hex(metadata_json),
    }
