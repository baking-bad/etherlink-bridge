#import "./common/types.mligo" "Types"
#import "./common/errors.mligo" "Errors"
#import "./common/utility.mligo" "Utility"


module RollupMock = struct
    (* This is helper contract used to lock/release tickets in the same
        way Rollup would do *)

    type ticket_id_t = address * Types.payload
    type message_t = {
        ticket_id : ticket_id_t;
        amount : nat;
        receiver : address;
    }

    type tickets_t = (ticket_id_t, Types.ticket_t) big_map
    type messages_t = (nat, message_t) big_map
    type next_id_t = nat

    type storage_t = {
        tickets : tickets_t;
        messages : messages_t;
        next_id : next_id_t;
    }
    type return_t = operation list * storage_t

    // TODO: consider rename to `deposit`?
    // TODO: mint `L2` ticket and record relations between this `L2` ticket and `L1` ticket
    [@entry] let save (ticket_with_data : Types.ticket_with_data_t) (store : storage_t) : return_t =
        (* This entrypoint used to emulate L1 rollup entrypoint used to
            deposit tickets *)
        let { tickets; messages; next_id } = store in
        let { ticket; routing_data } = ticket_with_data in
        let (ticketer, (payload, amount)), ticket_readed =
            Tezos.read_ticket ticket in
        let ticket_id = (ticketer, payload) in

        // TODO: Utilities.merge_tickets(new_ticket, tickets)
        // join tickets if contract already has one with the same payload:
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

        let l2_ticket = Utility.create_ticket (payload, amount) in
        let receiver_opt = Bytes.unpack routing_data.data in
        let receiver = Option.unopt receiver_opt in
        let receiver_contract = Utility.get_ticket_entrypoint (receiver) in
        let ticket_transfer_op =
            Tezos.transaction l2_ticket 0mutez receiver_contract in
        let updated_storage = {
            tickets = updated_tickets;
            messages = messages;
            next_id = next_id;
        } in
        [ticket_transfer_op], updated_storage

    // TODO: there should be `L2` entrypoint to `burn` ticket with some routing info
    // and allow anyone to release it on `L1` then
    // consider name: l2_burn?
    [@entry] let l2_burn (burn_ticket : Types.ticket_t) (store : storage_t) : return_t =
        (* This entrypoint used to emulate L2 rollup entrypoint used to
            burn L2 tickets and unlock L1 tickets *)
        let { tickets; messages; next_id } = store in
        let (ticketer, (payload, amount)), _ = Tezos.read_ticket burn_ticket in
        let _ = Utility.assert_address_is_self ticketer in
        let new_message = {
            ticket_id = (ticketer, payload);
            amount = amount;
            receiver = Tezos.get_sender ();
        } in
        let updated_store = {
            tickets = tickets;
            messages = Big_map.update next_id (Some new_message) messages;
            next_id = next_id + 1n;
        } in
        [], updated_store

    [@entry] let release (message_id : nat) (store : storage_t) : return_t =
        (* Releases ticket by message_id, this entrypoint emulates L1 rollup
            entrypoint which processes outbox L2->L1 transfer ticket message *)
        let { tickets; messages; next_id } = store in
        let message_opt, updated_messages =
            Big_map.get_and_update message_id None messages in
        let message = Option.unopt_with_error message_opt Errors.msg_not_found in
        let l1_ticket_opt, updated_tickets =
            Big_map.get_and_update message.ticket_id None tickets in
        let l1_ticket = Option.unopt_with_error l1_ticket_opt Errors.ticket_not_found in
        let (_, (_, amount)), l1_ticket_readed = Tezos.read_ticket l1_ticket in

        // TODO: split ticket if amount is greater than message.amount
        let receiver_contract = Utility.get_ticket_entrypoint message.receiver in
        let ticket_transfer_op = Tezos.transaction l1_ticket_readed 0mutez receiver_contract in

        let updated_store = {
            tickets = updated_tickets;
            messages = updated_messages;
            next_id = next_id
        } in
        [ticket_transfer_op], updated_store
end
