#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/routing-data.mligo" "RoutingData"


type route_t = (Ticket.t * RoutingData.t) -> operation list

type t = {
    routes : (string, route_t) big_map;
}

