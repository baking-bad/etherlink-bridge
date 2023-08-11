#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/errors.mligo" "Errors"
#import "../common/utility.mligo" "Utility"
#import "./storage.mligo" "Storage"


module Router = struct

    (*
        Router is a contract that routes tickets to different contracts
        based on the routing data.
    *)

    type return_t = operation list * Storage.t

    let route_to_l1_address
            (ticket, routing_data : Ticket.t * RoutingData.t)
            : operation list =
        let receiver = RoutingData.get_receiver routing_data in
        let receiver_contract = Ticket.get_ticket_entrypoint receiver in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez receiver_contract in
        [ticket_transfer_op]

    [@entry] let route
            (ticket, routing_data : Ticket.t * RoutingData.t)
            (store : Storage.t)
            : return_t =
        // TODO: should refund option be implemented here?
        let operations = route_to_l1_address (ticket, routing_data) in
        operations, store
end
