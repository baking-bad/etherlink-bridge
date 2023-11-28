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

// NOTE: this is entrypoint for ticketer%release
type release_params = [@layout:comb] {
    ticket: Ticket.t;
    receiver: address;
}
