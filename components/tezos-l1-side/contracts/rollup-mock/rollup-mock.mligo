#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "./storage.mligo" "Storage"
#import "./ticket-id.mligo" "TicketId"
#import "./message.mligo" "Message"
#import "../common/errors.mligo" "Errors"
#import "../common/utility.mligo" "Utility"


let send_ticket_to_router
        (ticket : Ticket.t)
        (router : address)
        (receiver : address)
        : operation =
    let payload : Entrypoints.withdraw_params = {
        receiver = receiver;
        ticket = ticket;
    } in
    let entry = Entrypoints.get_router_withdraw router in
    Tezos.transaction payload 0mutez entry


let send_ticket_to_receiver
        (ticket : Ticket.t)
        (receiver : address)
        : operation =
    let receiver_contract = Ticket.get_ticket_entrypoint receiver in
    Tezos.transaction ticket 0mutez receiver_contract


module RollupMock = struct
    (*
        This is helper contract used to deposit and release tickets on the
        L1 side in the similar way Rollup would do.
    *)

    type return_t = operation list * Storage.t

    [@entry] let rollup
            (rollup_entry : Entrypoints.rollup_entry)
            (store : Storage.t)
            : return_t =
        (* This entrypoint used to emulate L1 rollup entrypoint used to
            deposit tickets *)
        let {
            tickets;
            messages;
            next_message_id;
            metadata;
        } = store in
        let deposit = Entrypoints.unwrap_rollup_entrypoint rollup_entry in
        let { ticket = ticket; routing_info = _r } = deposit in
        let (ticketer, (payload, _amt)), ticket = Tezos.read_ticket ticket in
        let token_id = payload.0 in
        let ticket_id = { ticketer; token_id } in

        // Join tickets if contract already has one with the same payload:
        let updated_tickets = Storage.merge_tickets ticket_id ticket tickets in

        let updated_storage = {
            tickets = updated_tickets;
            messages = messages;
            next_message_id = next_message_id;
            metadata = metadata;
        } in
        [], updated_storage


    [@entry] let execute_outbox_message
            (message_id : nat)
            (store : Storage.t)
            : return_t =
        (* Releases ticket by message_id, this entrypoint emulates call to L1
            rollup which processes outbox L1 unlock ticket message *)
        let {
            tickets;
            messages;
            next_message_id;
            metadata;
        } = store in

        let message, updated_messages =
            Storage.pop_message message_id messages in
        let l1_ticket, updated_tickets =
            Storage.pop_ticket message.ticket_id tickets in
        let l1_ticket_send, l1_ticket_keep =
            Ticket.split_ticket l1_ticket message.amount in

        let receiver = RoutingData.get_receiver_l2_to_l1 message.routing_data in
        let ticket_transfer_op = match message.router with
        | Some router -> send_ticket_to_router l1_ticket_send router receiver
        | None -> send_ticket_to_receiver l1_ticket_send receiver in
        let updated_tickets =
            Big_map.update message.ticket_id (Some l1_ticket_keep) updated_tickets in

        let updated_store = {
            tickets = updated_tickets;
            messages = updated_messages;
            next_message_id = next_message_id;
            metadata = metadata;
        } in
        [ticket_transfer_op], updated_store


    [@entry] let create_outbox_message
            (new_message : Message.t)
            (store : Storage.t)
            : return_t =
        (* This entrypoint used to emulate L2 actions that changes rollup state
            and adds new outbox message that can be executed *)
        let {
            tickets;
            messages;
            next_message_id;
            metadata;
        } = store in

        let updated_store = {
            tickets = tickets;
            messages = Big_map.update next_message_id (Some new_message) messages;
            next_message_id = next_message_id + 1n;
            metadata = metadata;
        } in
        [], updated_store
end
