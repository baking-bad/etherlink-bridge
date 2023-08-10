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

        In the current implementation router supports different routing
        types. Each routing type is a lambda that takes ticket and routing
        data as arguments and returns a list of operations.

        Routing lambdas should be added to the router contract during
        the origination process. Each lambda should have a unique name.

        NOTE: maybe there will be only one type of routing for the
        transfer of tokens, in this case routing lambdas will be removed.
    *)

    type return_t = operation list * Storage.t

    let route_to_l1_address_lambda
            (ticket, routing_data : Ticket.t * RoutingData.t)
            : operation list =
        let receiver = RoutingData.get_receiver routing_data in
        let receiver_contract = Ticket.get_ticket_entrypoint receiver in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez receiver_contract in
        [ticket_transfer_op]

    // TODO: route_to_l1_address_and_unwrap_lambda implementation
    // (or maybe this is not needed if routing_data.info will be removed)

    let get_routing_func
            (routing_data : RoutingData.t)
            (store : Storage.t)
            : Storage.route_t =
        let route_type_opt = Map.find_opt "routing_type" routing_data.info in
        let route_type_bytes = match route_type_opt with
            | None -> failwith Errors.missing_routing_type
            | Some t -> t in
        let route_type : string = Option.unopt (Bytes.unpack route_type_bytes) in
        let route_func = match Big_map.find_opt route_type store.routes with
            | None -> failwith Errors.unknown_routing_type
            | Some f -> f in
        route_func

    [@entry] let route
            (ticket, routing_data : Ticket.t * RoutingData.t)
            (store : Storage.t)
            : return_t =
        // TODO: should refund option be implemented here?
        let route_func = get_routing_func routing_data store in
        let operations = route_func (ticket, routing_data) in
        operations, store
end
