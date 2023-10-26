type l1_to_l2_t = {
    wrapper : bytes;
    receiver : bytes;
}

type l2_to_l1_t = bytes

let get_receiver_l2_to_l1 (receiver : l2_to_l1_t) : address =
    Option.unopt (Bytes.unpack receiver)
