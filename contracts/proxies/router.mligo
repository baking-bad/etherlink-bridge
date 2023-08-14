#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/ticket.mligo" "Ticket"
#import "./generic.mligo" "Generic"
#import "./storage.mligo" "Storage"


(*
    This is proxy for implicit address to call for the
    RollupMock%l2_burn and RollupMock%l1_deposit entrypoints.

    Transfered type for these entrypoints is a pair of routing data
    and the ticket itself as payload.
*)

type data_t = RoutingData.t
type ticket_t = Ticket.t
type storage_t = data_t Storage.t
type parameter_t = (ticket_t, data_t) Generic.parameter_t

let make_ctx
        (ticket, data : ticket_t * data_t)
        : Entrypoints.ticket_with_routing_data =
    {
        routing_data = data;
        payload = ticket;
    }

let main : parameter_t -> storage_t -> operation list * storage_t =
    Generic.main make_ctx
