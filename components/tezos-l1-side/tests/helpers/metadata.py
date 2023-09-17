import json


DEFAULT_METADATA = {
    'version': '0.1.0',
    'name': 'Bridge Protocol Prototype',
    'description': 'The Bridge Protocol Prototype consists of contracts designed for communication between Tezos L1 and L2 rollups.',
    'interfaces': [
        'TZIP-016'
    ],
    'license': {
        'name': 'MIT'
    },
    'homepage': 'https://github.com/baking-bad/ticketer-proto'
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
