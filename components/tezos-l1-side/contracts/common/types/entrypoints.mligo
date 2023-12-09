#import "./routing-data.mligo" "RoutingData"
#import "./ticket.mligo" "Ticket"
#import "../errors.mligo" "Errors"


// NOTE: this is entrypoint for rollup%deposit
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

// NOTE: this is entrypoint for ticketer%release
// TODO: rename to ticketer_release_params?
type release_params = [@layout:comb] {
    ticket: Ticket.t;
    receiver: address;
}

type router_withdraw_params = [@layout:comb] {
    receiver: address;
    ticket: Ticket.t;
}

let get_router_withdraw (router : address) : router_withdraw_params contract =
    match Tezos.get_entrypoint_opt "%withdraw" router with
    | None -> failwith(Errors.router_entrypoint_not_found)
    | Some entry -> entry

// TODO: move all other entrypoint getters here?
