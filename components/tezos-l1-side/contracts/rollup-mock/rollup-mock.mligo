#import "../common/types/routing-data.mligo" "RoutingData"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "./storage.mligo" "Storage"
#import "./ticket-id.mligo" "TicketId"
#import "./message.mligo" "Message"
#import "../common/errors.mligo" "Errors"
#import "../common/utility.mligo" "Utility"


module RollupMock = struct
    (*
        This is helper contract used to deposit and release tickets in the
        similar way Rollup would do.

        This contract have both L1 and L2 sides. L1 side have two entrypoints:
        - l1_deposit - used to deposit tickets from L1 to L2
        - l1_release - used to call outbox message which releases tickets from
            L2 to L1

        L2 side have one entrypoint:
        - l2_burn - used to burn L2 tickets to unlock L1 tickets
    *)

    type return_t = operation list * Storage.t


    [@entry] let l1_deposit
            (ticket_with_routing_data : Entrypoints.ticket_with_routing_data)
            (store : Storage.t)
            : return_t =
        (* This entrypoint used to emulate L1 rollup entrypoint used to
            deposit tickets *)
        let {
            tickets;
            messages;
            next_message_id;
            next_l2_id;
            l2_ids;
            ticket_ids;
            metadata;
        } = store in
        let { payload = ticket; routing_data } = ticket_with_routing_data in
        let (ticketer, (payload, amount)), ticket = Tezos.read_ticket ticket in
        let token_id = payload.token_id in
        let ticket_id = { ticketer; token_id } in

        // Get or create L2 ticket id for given L1 ticket:
        let l2_id, updated_next_l2_id, updated_l2_ids, updated_ticket_ids =
            Storage.get_or_create_l2_id ticket_id next_l2_id l2_ids ticket_ids in

        // Join tickets if contract already has one with the same payload:
        let updated_tickets = Storage.merge_tickets ticket_id ticket tickets in

        // Create and transfer new ticket on L2:
        let l2_payload = Ticket.create_l2_payload payload ticketer l2_id in
        let l2_ticket = Ticket.create_ticket l2_payload amount in
        let receiver = RoutingData.get_receiver routing_data in
        let receiver_contract = Ticket.get_ticket_entrypoint receiver in
        let ticket_transfer_op =
            Tezos.transaction l2_ticket 0mutez receiver_contract in

        let updated_storage = {
            tickets = updated_tickets;
            messages = messages;
            next_message_id = next_message_id;
            next_l2_id = updated_next_l2_id;
            l2_ids = updated_l2_ids;
            ticket_ids = updated_ticket_ids;
            metadata = metadata;
        } in
        [ticket_transfer_op], updated_storage


    [@entry] let l1_release
            (message_id : nat)
            (store : Storage.t)
            : return_t =
        (* Releases ticket by message_id, this entrypoint emulates L1 rollup
            entrypoint which processes outbox L2->L1 transfer ticket message *)
        let {
            tickets;
            messages;
            next_message_id;
            next_l2_id;
            ticket_ids;
            l2_ids;
            metadata;
        } = store in

        let message, updated_messages =
            Storage.pop_message message_id messages in
        let l1_ticket, updated_tickets =
            Storage.pop_ticket message.ticket_id tickets in
        let l1_ticket_send, l1_ticket_keep =
            Ticket.split_ticket l1_ticket message.amount in

        let receiver = RoutingData.get_receiver message.routing_data in
        let receiver_contract = Ticket.get_ticket_entrypoint receiver in
        let ticket_transfer_op =
            Tezos.transaction l1_ticket_send 0mutez receiver_contract in
        let updated_tickets =
            Big_map.update message.ticket_id (Some l1_ticket_keep) updated_tickets in

        let updated_store = {
            tickets = updated_tickets;
            messages = updated_messages;
            next_message_id = next_message_id;
            next_l2_id = next_l2_id;
            l2_ids = l2_ids;
            ticket_ids = ticket_ids;
            metadata = metadata;
        } in
        [ticket_transfer_op], updated_store


    // TODO: consider renaming to l2_deposit and both process native L2
    // tickets and burning wrapped L1 tickets
    [@entry] let l2_burn
            (l2_burn_params : Entrypoints.ticket_with_routing_data)
            (store : Storage.t)
            : return_t =
        (* This entrypoint used to emulate L2 rollup entrypoint used to
            burn L2 tickets and unlock L1 tickets *)
        let {
            tickets;
            messages;
            next_message_id;
            next_l2_id;
            l2_ids;
            ticket_ids;
            metadata;
        } = store in

        let { payload = burn_ticket; routing_data } = l2_burn_params in
        let (ticketer, (payload, amount)), _ = Tezos.read_ticket burn_ticket in
        let ticket_id = Storage.get_ticket_id payload.token_id ticket_ids in
        let _ = Utility.assert_address_is_self ticketer in
        let new_message = {
            ticket_id = ticket_id;
            amount = amount;
            routing_data = routing_data;
        } in
        let updated_store = {
            tickets = tickets;
            messages = Big_map.update next_message_id (Some new_message) messages;
            next_message_id = next_message_id + 1n;
            next_l2_id = next_l2_id;
            l2_ids = l2_ids;
            ticket_ids = ticket_ids;
            metadata = metadata;
        } in
        [], updated_store
end
