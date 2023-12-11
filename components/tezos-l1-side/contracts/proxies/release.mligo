#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/ticket.mligo" "Ticket"
#import "./generic.mligo" "Generic"
#import "./storage.mligo" "Storage"


(*
    This is proxy for implicit address to call for the
    Ticketer%release entrypoint.

    Transfered type release entrypoint is a pair of receiver address
    and the ticket itself.
*)

type data_t = address
type ticket_t = Ticket.t
type storage_t = data_t Storage.t
type parameter_t = (ticket_t, data_t) Generic.parameter_t

let make_ctx
        (ticket, data : ticket_t * data_t)
        : Entrypoints.withdraw_params =
    {
        ticket = ticket;
        receiver = data;
    }

let main : parameter_t -> storage_t -> operation list * storage_t =
    Generic.main make_ctx
