type token_info = (string, bytes) map

type payload = [@layout:comb] {
    token_id : nat;
    token_info : bytes;
}

type routing_info = (string, bytes) map

type routing_data = [@layout:comb] {
    data : bytes;
    // TODO: make `refund_info : bytes` instead of `address` to
    // allow L2 -> L1 transfers for non-Tezos specific tokens?
    // ALTERNATIVE: `or address bytes`?
    refund_address : address;
    info : routing_info;
}

type ticket_t = payload ticket

type ticket_with_data_t = [@layout:comb] {
    ticket: ticket_t;
    routing_data: routing_data;
}
