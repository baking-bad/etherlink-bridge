from typing import TypedDict, Union, Literal
from tests.helpers.utility import pack
from typing import cast


address_or_bytes = Union[str, bytes]


class RoutingData(TypedDict):
    receiver: address_or_bytes
    refund_address: address_or_bytes
    info: dict[str, bytes]


RoutingType = Literal[
    "to_l1_address",
    "to_l2_address",
    "to_l1_address_and_unwrap"
]


def create_routing_data(
        sender: str,
        receiver: str,
        routing_type: RoutingType,
    ) -> RoutingData:
    """ Creates default routing data for the proxy contract """

    return cast(RoutingData, {
        'receiver': {'address': receiver},
        'refund_address': {'address': sender},
        'info': {
            'routing_type': pack(routing_type, 'string'),
            'version': pack('0.1.0', 'string'),
        }
    })
