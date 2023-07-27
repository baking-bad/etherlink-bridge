type token_info = (string, bytes) map

type payload = [@layout:comb] {
    token_id : nat;
    token_info : bytes;
}

type routing_info = (string, bytes) map

type routing_data = [@layout:comb] {
    data : bytes;
    refund_address : address;
    info : routing_info;
}

type ticket_t = payload ticket

(*
// TODO:
type ticket_with_data_t = {
    string_ticket: Types.ticket_t;
    routing_data: Types.routing_data;
}
*)
type ticket_with_data_t = ticket_t * routing_data
