#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"


(*
    Tools to manage a collection of tickets in the form of a big_map.
    Each ticket is identified by a unique id, which is a pair of a ticketer
    address and a token id. `save`, `pop` and `get` operations are provided.
*)

type id_t = {
    ticketer : address;
    token_id : nat;
}

type t = (id_t, Ticket.t) big_map

let read_id
        (ticket : Ticket.t)
        : id_t * Ticket.t =
    (* Reads ticket and returns its id and the ticket itself *)
    let (ticketer, (payload, _amt)), ticket = Tezos.Next.Ticket.read ticket in
    let token_id = payload.0 in
    let id = { ticketer; token_id } in
    id, ticket

let save
        (ticket : Ticket.t)
        (tickets : t)
        : t =
    (* Saves a ticket in the big_map, joining it with the existing one if any *)
    let id, ticket = read_id ticket in
    let ticket_opt, tickets = Big_map.get_and_update id None tickets in
    let ticket : Ticket.t = match ticket_opt with
        | Some stored_ticket ->
            let ticket_opt = Tezos.Next.Ticket.join (ticket, stored_ticket) in
            Option.value_with_error Errors.ticket_join_error ticket_opt
        | None -> ticket in
    Big_map.update id (Some ticket) tickets

let pop
        (id : id_t)
        (tickets : t)
        : Ticket.t * t =
    (* Pops a ticket from the big_map, returning it and the updated big_map *)
    let ticket_opt, tickets = Big_map.get_and_update id None tickets in
    let ticket = Option.value_with_error Errors.ticket_not_found ticket_opt in
    ticket, tickets

let get
        (id : id_t)
        (amount : nat)
        (tickets : t)
        : Ticket.t * t =
    (* Gets a ticket of some amount from the big_map *)
    let ticket_keep, tickets = pop id tickets in
    let ticket, ticket_keep = Ticket.split ticket_keep amount in
    let tickets = Big_map.update id (Some ticket_keep) tickets in
    ticket, tickets
