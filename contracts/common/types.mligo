type token_info = (string, bytes) map

type payload = {
    token_id : nat;
    token_info : bytes;
}

type routing_info = (string, bytes) map

type routing_data = {
    data : bytes;
    refund_address : address;
    info : routing_info;
}

type ticket_t = payload ticket
