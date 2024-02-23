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
