#import "./common/types.mligo" "Types"
#import "./common/errors.mligo" "Errors"
#import "./common/utility.mligo" "Utility"


// TODO: find a good name, RollupMock?
module Locker = struct
    (* This is helper contract used to lock/release tickets in the same
        way Rollup would do *)

    (*
    // NOTE: the following record with ticket fails to be compiled without
    //       ticket duplications
    type ticket_with_data_t = {
        string_ticket: Types.ticket_t;
        routing_data: Types.routing_data;
    }
    *)

    type ticket_with_data_t = Types.ticket_t * Types.routing_data
    type ticket_id_t = address * Types.payload
    type message_t = {
        ticket_id : ticket_id_t;
        amount : nat;
        receiver : address;
    }

    type storage_t = {
        tickets : (ticket_id_t, Types.ticket_t) big_map;
        outbox : (nat, message_t) big_map;
        next_id : nat;
    }
    type return_t = operation list * storage_t

    // TODO: this should be similar to L1 rollup entrypoint used to deposit tickets
    // TODO: consider name it `deposit`?
    // TODO: mint `L2` ticket and record relations between this `L2` ticket and `L1` ticket
    [@entry] let save (ticket_with_data : ticket_with_data_t) (store : storage_t) : return_t =
        let added_ticket, _ = ticket_with_data in
        let (ticketer, (payload, amount)), new_ticket = Tezos.read_ticket added_ticket in
        let ticket_id = (ticketer, payload) in
        // join tickets if contract already has one with the same payload:
        let stored_ticket_opt = Big_map.find_opt ticket_id store.tickets in
        let comb_ticket : Types.ticket_t = match stored_ticket_opt with
            | Some stored_ticket ->
                let joined_ticket_opt = Tezos.join_tickets (new_ticket, stored_ticket) in
                Option.unopt joined_ticket_opt
            | None -> new_ticket in
        let new_tickets = Big_map.update ticket_id (Some comb_ticket) store.tickets in

        let l2_ticket = Utility.create_ticket (payload, amount) in
        let sender = Tezos.get_sender () in
        let sender_contract = Utility.get_ticket_entrypoint (sender) in
        let ticket_transfer_op = Tezos.transaction l2_ticket 0mutez sender_contract in
        [], { store with tickets = new_tickets }
        // TODO: mint L2 ticket using routing data (or drop it and just use Tezos.sender)

    // TODO: there should be `L2` entrypoint to `burn` ticket with some routing info
    // and allow anyone to release it on `L1` then
    // consider name: l2_burn?
    [@entry] let l2_burn (burn_ticket : Types.ticket_t) (store : storage_t) : return_t =
        let (ticketer, (payload, amount)), _ = Tezos.read_ticket burn_ticket in
        let _ = Utility.assert_address_is_self ticketer in
        let new_message = {
            ticket_id = (ticketer, payload);
            amount = amount;
            receiver = Tezos.get_sender ();
        } in
        let updated_store = {
            store with
            outbox = Big_map.update store.next_id (Some new_message) store.outbox;
            next_id = store.next_id + 1n;
        } in
        [], updated_store

    // TODO: this should be similar to L1 rollup entrypoint that processes outbox message
    // parameter: `outbox_message_id`?
    [@entry] let release (message_id : nat) (store : storage_t) : return_t =
        (* Releases ticket by message_id *)
        let message_opt = Big_map.find_opt message_id store.outbox in
        let message = Option.unopt message_opt in
        let l1_ticket_opt = Big_map.find_opt message.ticket_id store.tickets in
        let l1_ticket = Option.unopt l1_ticket_opt in
        let (_, (_, amount)), _ = Tezos.read_ticket l1_ticket in
        // TODO: split ticket if amount is greater than message.amount
        let receiver_contract = Utility.get_ticket_entrypoint message.receiver in
        let ticket_transfer_op = Tezos.transaction l1_ticket 0mutez receiver_contract in
        let updated_store = {
            store with
            outbox = Big_map.remove message_id store.outbox;
        } in
        [ticket_transfer_op], updated_store
end
