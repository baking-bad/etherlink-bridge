#import "./routing-data.mligo" "RoutingData"
#import "./ticket.mligo" "Ticket"
#import "../errors.mligo" "Errors"


// NOTE: this is entrypoint for rollup%deposit
type ticket_with_routing_data = [@layout:comb] {
    payload: Ticket.t;
    routing_data: RoutingData.l1_to_l2_t;
}

// NOTE: this is entrypoint for ticketer%release
type release_params = [@layout:comb] {
    ticket: Ticket.t;
    receiver: address;
}
