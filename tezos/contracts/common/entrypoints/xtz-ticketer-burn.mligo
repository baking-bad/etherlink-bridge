#import "../errors.mligo" "Errors"
#import "../types/ticket.mligo" "Ticket"


// TODO: add docstring
type t = address * Ticket.t

let get (xtz_ticketer : address) : t contract =
    match Tezos.get_entrypoint_opt "%burn" xtz_ticketer with
    | None -> failwith(Errors.invalid_xtz_ticketer)
    | Some entry -> entry

let send
        (xtz_ticketer : address)
        (receiver_and_ticket : t) : operation =
    let entry = get xtz_ticketer in
    Tezos.Next.Operation.transaction receiver_and_ticket 0mutez entry
