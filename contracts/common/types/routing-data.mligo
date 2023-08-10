type routing_info = (string, bytes) map

type address_or_bytes = [@layout:comb]
    | Address of address
    | Bytes of bytes

type t = [@layout:comb] {
    receiver : address_or_bytes;
    sender : address_or_bytes;
    // TODO: consider removing roiting_info and limit the bridge logic
    // to simply transferring the token to the given address
    info : routing_info;
}

let get_receiver (data : t) : address =
    match data.receiver with
        | Address (receiver_address) -> receiver_address
        | Bytes (receiver_bytes) ->
            let receiver_opt = Bytes.unpack receiver_bytes in
            Option.unopt receiver_opt
