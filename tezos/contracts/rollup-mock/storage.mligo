#import "./message.mligo" "Message"
#import "./ticket-id.mligo" "TicketId"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"


type tickets_t = (TicketId.t, Ticket.t) big_map
// TODO: replace message_id_t with commitment hash + output proof?
type message_id_t = nat
type messages_t = (message_id_t, Message.t) big_map

type t = {
    tickets : tickets_t;
    messages : messages_t;
    next_message_id : message_id_t;
    metadata : (string, bytes) big_map;
}


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


let pop_message
        (message_id : message_id_t)
        (messages : messages_t)
        : Message.t * messages_t =
    let message_opt, updated_messages =
        Big_map.get_and_update message_id None messages in
    let message = Option.unopt_with_error message_opt Errors.msg_not_found
    in message, updated_messages


let pop_ticket
        (ticket_id : TicketId.t)
        (tickets : tickets_t)
        : Ticket.t * tickets_t =
    let ticket_opt, updated_tickets =
        Big_map.get_and_update ticket_id None tickets in
    let ticket =
        Option.unopt_with_error ticket_opt Errors.ticket_not_found in
    ticket, updated_tickets
