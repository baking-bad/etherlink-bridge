#import "./common/tokens/index.mligo" "Token"
#import "./common/types.mligo" "Types"
#import "./common/errors.mligo" "Errors"
#import "./common/utility.mligo" "Utility"


// TODO: why have one router for all route types, maybe it is better to have
// different router contracts for different route types?
// This would be easier to implement but maybe harder to maintain

module Router = struct

    type route_t = (Types.ticket_t * Types.routing_data) -> operation list

    type storage = {
        routes : (string, route_t) big_map;
    }
    type return = operation list * storage

    let route_to_sender_lambda
            (ticket, _routing_data : Types.ticket_t * Types.routing_data)
            : operation list =
        let sender = Tezos.get_sender () in
        let sender_contract = Utility.get_ticket_entrypoint (sender) in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez sender_contract in
        [ticket_transfer_op]

    // TODO: route_to_l1_address_lambda implementation
    // TODO: some route that will unpack routing lambda from routing_info?

    [@entry] let route
            (ticket, routing_data : Types.ticket_t * Types.routing_data)
            (store : storage)
            : return =
        // TODO: should refund option be implemented here?
        // TODO: consider making some function to get routing info by key?
        // TODO: should routing with lambda included in routing_info be processed
        //       here as default routing case [instead of having some routing_type
        //       for this?]
        let route_type_opt = Map.find_opt "routing_type" routing_data.info in
        let route_type_bytes = match route_type_opt with
            | None -> failwith Errors.missing_routing_type
            | Some t -> t in
        let route_type : string = Option.unopt (Bytes.unpack route_type_bytes) in
        let route_func = match Big_map.find_opt route_type store.routes with
            | None -> failwith Errors.unknown_routing_type
            | Some f -> f in
        let operations = route_func (ticket, routing_data) in
        operations, store
end
