#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/ticket.mligo" "Ticket"
#import "./generic.mligo" "Generic"
#import "./storage.mligo" "Storage"


(*
    This is proxy for implicit address to call the
    RollupMock%deposit entrypoint.

    Transfered type for these entrypoints is a pair of routing data
    and the ticket itself as payload.
*)

type data_t = RoutingData.l1_to_l2_t
type ticket_t = Ticket.t
type storage_t = data_t Storage.t
type parameter_t = (ticket_t, data_t) Generic.parameter_t

let make_ctx
        (ticket, data : ticket_t * data_t)
        : Entrypoints.rollup_entry =
    let deposit : Entrypoints.deposit = {
        routing_info = data;
        ticket = ticket;
    } in
    let deposit_or_bytes : Entrypoints.deposit_or_bytes = (M_left deposit) in
    let payload : Entrypoints.rollup_entry = (M_left deposit_or_bytes) in payload

let main : parameter_t -> storage_t -> operation list * storage_t =
    Generic.main make_ctx
