#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/ticket.mligo" "Ticket"
#import "./generic.mligo" "Generic"
#import "./storage.mligo" "Storage"


(*
    This is proxy for implicit address to call for the
    RollupMock%l2_burn entrypoint.

    Transfered type for L2 burn is a pair of routing data,
    the router address which will process L1 ticket unlock
    and the ticket itself.
*)

type data_t = {
    routing_data : RoutingData.t;
    router : address;
}
type ticket_t = Ticket.t
type storage_t = data_t Storage.t
type parameter_t = (ticket_t, data_t) Generic.parameter_t

let make_ctx
        (ticket, data : ticket_t * data_t)
        : Entrypoints.l2_burn_params =
    {
        ticket = ticket;
        routing_data = data.routing_data;
        router = data.router;
    }

let main : parameter_t -> storage_t -> operation list * storage_t =
    Generic.main make_ctx
