#import "./routing-data.mligo" "RoutingData"
#import "./ticket.mligo" "Ticket"
#import "../errors.mligo" "Errors"


// NOTE: this is entrypoint for rollup%l1_deposit, router%route and rollup%l2_burn
type ticket_with_routing_data = [@layout:comb] {
    payload: Ticket.t;
    routing_data: RoutingData.t;
}

// NOTE: this is entrypoint for ticketer%release
type release_params = [@layout:comb] {
    ticket: Ticket.t;
    receiver: address;
}
