from typing import TypedDict, Union, Literal
from tests.helpers.utility import pack
from typing import cast


address_or_bytes = Union[str, bytes]


class RoutingData(TypedDict):
    receiver: address_or_bytes
    refund_address: address_or_bytes


def create_routing_data(
        sender: str,
        receiver: str,
    ) -> RoutingData:
    """ Creates default routing data for the proxy contract """

    return cast(RoutingData, {
        'receiver': {'address': receiver},
        'sender': {'address': sender},
    })
