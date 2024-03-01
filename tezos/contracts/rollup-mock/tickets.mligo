#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"


type id_t = {
    ticketer : address;
    token_id : nat;
}

let read_id
        (ticket : Ticket.t)
        : id_t * Ticket.t =
    let (ticketer, (payload, _amt)), ticket = Tezos.read_ticket ticket in
    let token_id = payload.0 in
    let id = { ticketer; token_id } in
    id, ticket

type t = (id_t, Ticket.t) big_map

let save
        (ticket : Ticket.t)
        (tickets : t)
        : t =
    let id, ticket = read_id ticket in
    let ticket_opt, tickets = Big_map.get_and_update id None tickets in
    let ticket : Ticket.t = match ticket_opt with
        | Some stored_ticket ->
            let ticket = Tezos.join_tickets (ticket, stored_ticket) in
            Option.unopt ticket
        | None -> ticket in
    Big_map.update id (Some ticket) tickets

let pop
        (id : id_t)
        (tickets : t)
        : Ticket.t * t =
    let ticket_opt, tickets = Big_map.get_and_update id None tickets in
    let ticket = Option.unopt_with_error ticket_opt Errors.ticket_not_found in
    ticket, tickets

let get
        (id : id_t)
        (amount : nat)
        (tickets : t)
        : Ticket.t * t =
    let ticket_keep, tickets = pop id tickets in
    let ticket, ticket_keep = Ticket.split ticket_keep amount in
    let tickets = Big_map.update id (Some ticket_keep) tickets in
    ticket, tickets
