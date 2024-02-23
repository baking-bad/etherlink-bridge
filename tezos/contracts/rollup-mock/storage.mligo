#import "../common/types/ticket.mligo" "Ticket"
#import "../common/errors.mligo" "Errors"
#import "./message.mligo" "Message"
#import "./tickets.mligo" "Tickets"


// TODO: replace message_id_t with commitment hash + output proof?
type message_id_t = nat
type messages_t = (message_id_t, Message.t) big_map

type t = {
    tickets : Tickets.t;
    messages : messages_t;
    next_message_id : message_id_t;
    metadata : (string, bytes) big_map;
}

let pop_message
        (message_id : message_id_t)
        (messages : messages_t)
        : Message.t * messages_t =
    let message_opt, updated_messages =
        Big_map.get_and_update message_id None messages in
    let message = Option.unopt_with_error message_opt Errors.msg_not_found
    in message, updated_messages
