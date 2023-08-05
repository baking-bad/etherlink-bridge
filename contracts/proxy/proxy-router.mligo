#import "../common/types.mligo" "Types"
#import "./proxy-generic.mligo" "Proxy"
#import "./storage.mligo" "Storage"


type data_t = Types.routing_data
type ticket_t = Types.ticket_t
type storage_t = data_t Storage.t
type entrypoint_t = Types.ticket_with_data_t
type parameter_t = (ticket_t, data_t) Proxy.parameter_t

let make_ctx (ticket, data : ticket_t * data_t) : entrypoint_t = {
    routing_data = data;
    ticket = ticket;
}

let main : parameter_t -> storage_t -> operation list * storage_t =
   Proxy.main make_ctx
