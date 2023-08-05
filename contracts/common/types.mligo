type token_info = (string, bytes) map

type payload = [@layout:comb] {
    token_id : nat;
    token_info : bytes option;
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
// NOTE: this is entrypoint for rollup%deposit and for router%process
//       consider renaming to `...entrypoint...` OR `ticket_with_routing_data_t`
type ticket_with_data_t = [@layout:comb] {
    // TODO: rename ticket -> payload
    ticket: ticket_t;
    routing_data: routing_data;
}

// NOTE: this is entrypoint for ticketer%release
type ticket_with_receiver_t = [@layout:comb] {
    ticket: ticket_t;
    receiver: address;
}
