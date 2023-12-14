#import "./routing-data.mligo" "RoutingData"
#import "./ticket.mligo" "Ticket"
#import "../tokens/index.mligo" "Token"
#import "../errors.mligo" "Errors"


(*
    `rollup_entry` is an interface for the Ehterlink smart rollup.
    As far as smart rollups currently do not support entrypoints (like
    smart contracts), to access `deposit` entrypoint, it needs to be
    constructed from the full contract type:
*)
type deposit = [@layout:comb] {
    routing_info: RoutingData.l1_to_l2_t;
    ticket: Ticket.t;
}

type deposit_or_bytes = (
    deposit,
    "deposit",
    bytes,
    "b"
) michelson_or

type rollup_entry = (
    deposit_or_bytes,
    "",
    bytes,
    "c"
) michelson_or

let unwrap_rollup_entrypoint
        (rollup_entry : rollup_entry)
        : deposit =
    let deposit = match rollup_entry with
    | M_right _bytes -> failwith(Errors.wrong_rollup_entrypoint)
    | M_left deposit_or_bytes -> (
        match deposit_or_bytes with
        | M_left deposit -> deposit
        | M_right _bytes -> failwith(Errors.wrong_rollup_entrypoint)
    ) in deposit

let wrap_rollup_entrypoint
        (deposit : deposit)
        : rollup_entry =
    M_left (M_left deposit)

(* `deposit_params` is deposit interface for the Ticketer contract: *)
type deposit_params = nat

(*
    `withdraw_params` is router interface that used for redirecting
    tickets during withdrawal from the Etherlink rollup:
 *)
type withdraw_params = [@layout:comb] {
    receiver: address;
    ticket: Ticket.t;
}

let get_router_withdraw (router : address) : withdraw_params contract =
    match Tezos.get_entrypoint_opt "%withdraw" router with
    | None -> failwith(Errors.router_entrypoint_not_found)
    | Some entry -> entry


let get_ticketer_deposit (router : address) : deposit_params contract =
    match Tezos.get_entrypoint_opt "%deposit" router with
    | None -> failwith(Errors.router_entrypoint_not_found)
    | Some entry -> entry


let get_rollup_deposit (rollup : address) : rollup_entry contract =
    match Tezos.get_contract_opt rollup with
    | None -> failwith Errors.rollup_deposit_not_found
    | Some entry -> entry
