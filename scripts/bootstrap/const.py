MAINNET_L1_RPC_URL = 'https://rpc.tzkt.io'
MAINNET_TZKT_API_URL = 'https://api.tzkt.io/v1'
NETWORK_DEFAULTS = [
    {
        'name': 'Parisnet',
        'l1_rpc_url': 'https://rpc.tzkt.io/parisnet',
        'smart_rollup_address': 'sr1GBHEgzZmpWH4URqshZEZFCxBpqzi6ahvL',
        'l1_private_key': 'edskS9uWwJB8U4NiD5YcV8SJvveA1ps7iTXRChXMrHn6fyMv8FpMoA6M855o6bSYBxaCtAPDfe9vK6hkiwGfoi7njK6M3PBSVP',
        'l2_private_key': '8636c473b431be57109d4153735315a5cdf36b3841eb2cfa80b75b3dcd2d941a',
        'l2_rpc_url': 'https://etherlink.dipdup.net',
        'l1_testrunner_account': 'tz1TZDn2ZK35UnEjyuGQRVeM2NC5tQScJLpQ',
    },
    {
        'name': 'Ghostnet',
        'l1_rpc_url': 'https://rpc.tzkt.io/ghostnet',
    },
    # {
    #     'name': 'Mainnet',
    #     'l1_rpc_url': MAINNET_L1_RPC_URL,
    #     'is_mainnet': True,
    # },
    {
        'name': 'Private Network',
    },
]

KERNEL_ADDRESS = '0x0000000000000000000000000000000000000000'
DEFAULT_TOKEN_ID = 0

MAINNET_WHITELIST = [
    'KT1PWx2mnDueood7fEmfbBDKx1D9BAnnXitn_0',  # tzBTC
    'KT1AafHA1C1vk959wvHWBispY9Y2f3fxBUUo_0',  # Sirius
    'KT1XnTn74bUtxHfDtBmm2bGZAQfhPbvKWR8o_0',  # USDt
]
