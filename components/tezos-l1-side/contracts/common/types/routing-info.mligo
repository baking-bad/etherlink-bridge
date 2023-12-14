(*
    L1 to L2 routing info is two standard Ethereum addresses in raw form (H160):
    `| receiver | proxy |` 40 bytes payload
*)
type l1_to_l2_t = bytes

(*
    L2 to L1 routing info is two Tezos addresses forged and concatenated:
    `| receiver | proxy |` 44 bytes payload
*)
type l2_to_l1_t = bytes

(*
    NOTE: in this rollup mock implementation proxy address provided
    during the outbox message creation and it is not required to be
    decoded from the routing data.

    TODO: consider parsing the receiver and router addresses from the
    routing_data instead?
*)
let get_receiver_l2_to_l1 (receiver : l2_to_l1_t) : address =
    Option.unopt (Bytes.unpack receiver)
