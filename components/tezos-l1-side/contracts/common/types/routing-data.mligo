type t = bytes

let get_receiver (receiver : t) : address =
    Option.unopt (Bytes.unpack receiver)
