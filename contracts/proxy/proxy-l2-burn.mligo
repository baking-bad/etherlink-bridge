#import "../common/types.mligo" "Types"
#import "./proxy-generic.mligo" "Proxy"
#import "./storage.mligo" "Storage"


// Transfered type for L2 burn is a pair of routing data and router address:
type data_t = {
    routing_data : Types.routing_data;
    router : address;
}
type ticket_t = Types.ticket_t
type storage_t = data_t Storage.t
type entrypoint_t = Types.l2_burn_params
type parameter_t = (ticket_t, data_t) Proxy.parameter_t

let make_ctx (ticket, data : ticket_t * data_t) : entrypoint_t = {
    ticket = ticket;
    routing_data = data.routing_data;
    router = data.router;
}

let main : parameter_t -> storage_t -> operation list * storage_t =
   Proxy.main make_ctx
