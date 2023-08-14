type address_or_bytes = [@layout:comb]
    | Address of address
    | Bytes of bytes

type t = address_or_bytes

let get_receiver (receiver : t) : address =
    match receiver with
        | Address (receiver_address) -> receiver_address
        | Bytes (receiver_bytes) ->
            let receiver_opt = Bytes.unpack receiver_bytes in
            Option.unopt receiver_opt
