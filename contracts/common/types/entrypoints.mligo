#import "./routing-data.mligo" "RoutingData"
#import "./ticket.mligo" "Ticket"


// NOTE: this is entrypoint for rollup%l1_deposit and router%route
type ticket_with_routing_data = [@layout:comb] {
    payload: Ticket.t;
    routing_data: RoutingData.t;
}

// NOTE: this is entrypoint for ticketer%release
type release_params = [@layout:comb] {
    ticket: Ticket.t;
    receiver: address;
}

// NOTE: this is entrypoint for rollup%l2_burn
type l2_burn_params = [@layout:comb] {
    ticket : Ticket.t;
    routing_data : RoutingData.t;
    router : address;
}
