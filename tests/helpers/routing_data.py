from typing import TypedDict
from tests.helpers.utility import pack
from typing import cast


class RoutingData(TypedDict):
    data: bytes
    refund_address: str
    info: dict[str, bytes]


def create_routing_data(refund_address: str, l2_address: str) -> RoutingData:
    """ Creates default routing data for the proxy contract with
        l2_address as destination encoded in the data field """

    return cast(RoutingData, {
        'data': pack(l2_address, 'address'),
        'refund_address': refund_address,
        'info': {
            'routing_type': pack('to_l2_address', 'string'),
            'data_type': pack('address', 'string'),
            'version': pack('0.1.0', 'string'),
        }
    })
