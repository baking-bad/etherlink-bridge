#import "./routing-data.mligo" "RoutingData"
#import "./ticket.mligo" "Ticket"
#import "../tokens/index.mligo" "Token"
#import "../errors.mligo" "Errors"


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

// This is deposit interface for the Ehterlink smart rollup:
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

// This is deposit interface for the Ticketer contract:
type deposit_params = [@layout:comb] {
    token: Token.t;
    amount: nat;
}

// This is withdraw interface that used for withdrawal transactions
// on the Etherlink rollup initiated by executing outbox message:
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

// TODO: move all other entrypoint getters here?
