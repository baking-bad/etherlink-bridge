#import "./message.mligo" "Message"
#import "./ticket-id.mligo" "TicketId"
#import "../common/types/ticket.mligo" "Ticket"


type l2_ids_t = (TicketId.t, nat) big_map
type ticket_ids_t = (nat, TicketId.t) big_map
type tickets_t = (TicketId.t, Ticket.t) big_map

type t = {
    tickets : tickets_t;
    messages : (nat, Message.t) big_map;
    next_message_id : nat;
    next_l2_id : nat;
    l2_ids : l2_ids_t;
    ticket_ids : ticket_ids_t;
}


let get_or_create_l2_id
        (ticket_id : TicketId.t)
        (next_l2_id : nat)
        (l2_ids : l2_ids_t)
        (ticket_ids : ticket_ids_t)
        : nat * nat * l2_ids_t * ticket_ids_t =
    match Big_map.find_opt ticket_id l2_ids with
    | Some l2_id -> l2_id, next_l2_id, l2_ids, ticket_ids
    | None ->
        let l2_id = next_l2_id in
        let updated_l2_ids = Big_map.update ticket_id (Some l2_id) l2_ids in
        let updated_ticket_ids = Big_map.update l2_id (Some ticket_id) ticket_ids in
        l2_id, next_l2_id + 1n, updated_l2_ids, updated_ticket_ids


let merge_tickets
        (ticket_id : TicketId.t)
        (ticket_readed : Ticket.t)
        (tickets : tickets_t)
        : tickets_t =
    let stored_ticket_opt, updated_tickets =
        Big_map.get_and_update ticket_id None tickets in
    let comb_ticket : Ticket.t = match stored_ticket_opt with
        | Some stored_ticket ->
            let joined_ticket_opt =
                Tezos.join_tickets (ticket_readed, stored_ticket) in
            Option.unopt joined_ticket_opt
        | None -> ticket_readed in
    Big_map.update ticket_id (Some comb_ticket) updated_tickets
