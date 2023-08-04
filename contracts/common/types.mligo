type token_info = (string, bytes) map

type payload = [@layout:comb] {
    token_id : nat;
    token_info : bytes;
}

type routing_info = (string, bytes) map

type address_or_bytes = [@layout:comb]
    | Address of address
    | Bytes of bytes

type routing_data = [@layout:comb] {
    // TODO: consider renaming to `receiver_address`?
    receiver : address_or_bytes;
    refund_address : address_or_bytes;
    info : routing_info;
}

type ticket_t = payload ticket

// TODO: this type can be generalized to be used as AMB type
type ticket_with_data_t = [@layout:comb] {
    // TODO: rename ticket -> payload
    ticket: ticket_t;
    routing_data: routing_data;
}
