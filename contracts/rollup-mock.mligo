#import "./common/types.mligo" "Types"
#import "./common/errors.mligo" "Errors"
#import "./common/utility.mligo" "Utility"


module RollupMock = struct
    (* This is helper contract used to lock/release tickets in the same
        way Rollup would do *)

    type ticket_id_t = {
        ticketer : address;
        token_id : nat;
    }

    type message_t = {
        ticket_id : ticket_id_t;
        amount : nat;
        receiver : address;
        // TODO: add routing_info or some data about L1 contract which
        // should process message
    }

    type storage_t = {
        tickets : (ticket_id_t, Types.ticket_t) big_map;
        messages : (nat, message_t) big_map;
        next_message_id : nat;
        next_l2_id : nat;
        l2_ids : (ticket_id_t, nat) big_map;
        ticket_ids : (nat, ticket_id_t) big_map;
    }
    type return_t = operation list * storage_t

    // TODO: consider rename to `deposit`?
    [@entry] let save (ticket_with_data : Types.ticket_with_data_t) (store : storage_t) : return_t =
        (* This entrypoint used to emulate L1 rollup entrypoint used to
            deposit tickets *)
        let {
            tickets;
            messages;
            next_message_id;
            next_l2_id;
            l2_ids;
            ticket_ids
        } = store in
        let { ticket; routing_data } = ticket_with_data in
        let (ticketer, (payload, amount)), ticket_readed =
            Tezos.read_ticket ticket in
        let token_id = payload.token_id in
        let ticket_id = { ticketer; token_id } in

        // join tickets if contract already has one with the same payload:
        // TODO: Storage.get_or_create_l2_id(ticket_id, next_l2_id, l2_ids)
        let l2_id, updated_next_l2_id, updated_l2_ids, updated_ticket_ids =
            match Big_map.find_opt ticket_id l2_ids with
            | Some l2_id -> l2_id, next_l2_id, l2_ids, ticket_ids
            | None ->
                let l2_id = next_l2_id in
                let updated_l2_ids = Big_map.update ticket_id (Some l2_id) l2_ids in
                let updated_ticket_ids = Big_map.update l2_id (Some ticket_id) ticket_ids in
                l2_id, next_l2_id + 1n, updated_l2_ids, updated_ticket_ids in

        // TODO: Utilities.merge_tickets(new_ticket, tickets)
        let stored_ticket_opt, updated_tickets =
            Big_map.get_and_update ticket_id None tickets in
        let comb_ticket : Types.ticket_t = match stored_ticket_opt with
            | Some stored_ticket ->
                let joined_ticket_opt =
                    Tezos.join_tickets (ticket_readed, stored_ticket) in
                Option.unopt joined_ticket_opt
            | None -> ticket_readed in
        let updated_tickets =
            Big_map.update ticket_id (Some comb_ticket) updated_tickets in

        // TODO: patch payload.token_info and add ticketer and L1 ticketer id to it
        //       maybe some separate function to .create_l2_payload(payload, ticketer, l2_id)
        let l2_payload = {
            token_id = l2_id;
            token_info = payload.token_info;
        } in

        let l2_ticket = Utility.create_ticket (l2_payload, amount) in
        let receiver_opt = Bytes.unpack routing_data.data in
        let receiver = Option.unopt receiver_opt in
        let receiver_contract = Utility.get_ticket_entrypoint (receiver) in
        let ticket_transfer_op =
            Tezos.transaction l2_ticket 0mutez receiver_contract in

        let updated_storage = {
            tickets = updated_tickets;
            messages = messages;
            next_message_id = next_message_id;
            next_l2_id = updated_next_l2_id;
            l2_ids = updated_l2_ids;
            ticket_ids = updated_ticket_ids;
        } in
        [ticket_transfer_op], updated_storage

    [@entry] let l2_burn (burn_ticket : Types.ticket_t) (store : storage_t) : return_t =
        (* This entrypoint used to emulate L2 rollup entrypoint used to
            burn L2 tickets and unlock L1 tickets *)
        let {
            tickets;
            messages;
            next_message_id;
            next_l2_id;
            l2_ids;
            ticket_ids;
        } = store in

        let (ticketer, (payload, amount)), _ = Tezos.read_ticket burn_ticket in
        let l2_id = payload.token_id in
        let ticket_id_opt = Big_map.find_opt l2_id ticket_ids in
        let ticket_id = Option.unopt ticket_id_opt in
        let _ = Utility.assert_address_is_self ticketer in
        let new_message = {
            ticket_id = ticket_id;
            amount = amount;
            receiver = Tezos.get_sender ();
        } in
        let updated_store = {
            tickets = tickets;
            messages = Big_map.update next_message_id (Some new_message) messages;
            next_message_id = next_message_id + 1n;
            next_l2_id = next_l2_id;
            l2_ids = l2_ids;
            ticket_ids = ticket_ids;
        } in
        [], updated_store

    [@entry] let release (message_id : nat) (store : storage_t) : return_t =
        (* Releases ticket by message_id, this entrypoint emulates L1 rollup
            entrypoint which processes outbox L2->L1 transfer ticket message *)
        let { tickets; messages; next_message_id; next_l2_id; ticket_ids; l2_ids } = store in
        let message_opt, updated_messages =
            Big_map.get_and_update message_id None messages in
        let message = Option.unopt_with_error message_opt Errors.msg_not_found in
        let l1_ticket_opt, updated_tickets =
            Big_map.get_and_update message.ticket_id None tickets in
        let l1_ticket = Option.unopt_with_error l1_ticket_opt Errors.ticket_not_found in
        let (_, (_, amount)), l1_ticket_readed = Tezos.read_ticket l1_ticket in

        // TODO: split ticket if amount is greater than message.amount
        let keep_amount =
            if amount >= message.amount then abs(amount - message.amount)
            else failwith Errors.insufficient_amount in
        let l1_ticket_send, l1_ticket_keep =
            match Tezos.split_ticket l1_ticket_readed (message.amount, keep_amount) with
            | Some split_tickets -> split_tickets
            | None -> failwith Errors.irreducible_amount in
        let receiver_contract = Utility.get_ticket_entrypoint message.receiver in
        let ticket_transfer_op = Tezos.transaction l1_ticket_send 0mutez receiver_contract in
        // TODO: save l1_ticket_keep to the storage

        let updated_store = {
            tickets = updated_tickets;
            messages = updated_messages;
            next_message_id = next_message_id;
            next_l2_id = next_l2_id;
            l2_ids = l2_ids;
            ticket_ids = ticket_ids;
        } in
        [ticket_transfer_op], updated_store
end
