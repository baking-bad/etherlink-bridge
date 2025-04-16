#import "../types/ticket.mligo" "Ticket"
#import "../types/routing-info.mligo" "RoutingInfo"
#import "../errors.mligo" "Errors"


(*
    `rollup-deposit` is an interface for the Ehterlink smart rollup.
    As far as smart rollups currently do not support entrypoints (like
    smart contracts), to access the `deposit` entrypoint, it needs to be
    constructed from the full contract type:
    - routing_info: routing information for the deposit (20 or 40 bytes
        representing a receiver and an ERC20 token address concatinated)
    - ticket: a ticket to be deposited
*)
type deposit_t = [@layout:comb] {
    routing_info: RoutingInfo.l1_to_l2_t;
    ticket: Ticket.t;
}

type deposit_or_bytes_t = (
    deposit_t,
    "deposit",
    bytes,
    "b"
) michelson_or

type t = (
    deposit_or_bytes_t,
    "",
    bytes,
    "c"
) michelson_or

let unwrap
        (rollup_entry : t)
        : deposit_t =
    let deposit = match rollup_entry with
    | M_right _bytes -> failwith(Errors.wrong_rollup_entrypoint)
    | M_left deposit_or_bytes -> (
        match deposit_or_bytes with
        | M_left deposit -> deposit
        | M_right _bytes -> failwith(Errors.wrong_rollup_entrypoint)
    ) in deposit

let wrap
        (deposit : deposit_t)
        : t =
    M_left (M_left deposit)

let get (rollup : address) : t contract =
    match Tezos.get_contract_opt rollup with
    | None -> failwith Errors.rollup_deposit_not_found
    | Some entry -> entry

let send
        (rollup : address)
        (deposit : deposit_t)
        : operation =
    let payload = wrap deposit in
    let entry = get rollup in
    Tezos.Next.Operation.transaction payload 0mutez entry
