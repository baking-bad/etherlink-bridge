#import "../common/types/routing-info.mligo" "RoutingInfo"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/entrypoints/router-withdraw.mligo" "WithdrawEntry"
#import "../common/entrypoints/rollup-deposit.mligo" "DepositEntry"
#import "./storage.mligo" "Storage"
#import "./message.mligo" "Message"


module RollupMock = struct
    (*
        RollupMock is helper contract used to deposit and release tickets on
        the L1 side in the similar way Rollup would do.
    *)

    let send_ticket_to_router
            (ticket : Ticket.t)
            (router : address)
            (receiver : address)
            : operation =
        let entry = WithdrawEntry.get router in
        Tezos.transaction { receiver; ticket } 0mutez entry

    type return_t = operation list * Storage.t

    [@entry] let rollup
            (rollup_entry : DepositEntry.t)
            (store : Storage.t)
            : return_t =
        (*
            `rollup` entrypoint emulates L1 rollup full entrypoint.
            It allows to deposit tickets the same way as L1 rollup would do.

            It merges together deposited tickets with the same ticketer
            and token_id from content.
        *)

        let { tickets; messages; next_message_id; metadata } = store in
        let deposit = DepositEntry.unwrap rollup_entry in
        let { ticket = ticket; routing_info = _r } = deposit in
        let (ticketer, (payload, _amt)), ticket = Tezos.read_ticket ticket in
        let token_id = payload.0 in
        let ticket_id = { ticketer; token_id } in
        let tickets = Storage.merge_tickets ticket_id ticket tickets in
        let upd_store = { tickets; messages; next_message_id; metadata; } in
        [], upd_store

    [@entry] let create_outbox_message
            (new_message : Message.t)
            (store : Storage.t)
            : return_t =
        (*
            `create_outbox_message` allows to emulate L2 actions that changes
            rollup state and adds new outbox message that can be executed
        *)

        let { tickets; messages; next_message_id; metadata } = store in
        let messages = Big_map.update next_message_id (Some new_message) messages in
        let next_message_id = next_message_id + 1n in
        let upd_store = { tickets; messages; next_message_id; metadata } in
        [], upd_store

    [@entry] let execute_outbox_message
            (message_id : nat)
            (store : Storage.t)
            : return_t =
        (*
            `execute_outbox_message` allows to release tickets the same way
            as L1 rollup would do when someone triggered L1 outbox message
            execution. It will call the withdraw router contract with the
            ticket and receiver address.
        *)

        let { tickets; messages; next_message_id; metadata } = store in
        let message, messages = Storage.pop_message message_id messages in
        let { ticket_id; router; amount; routing_data } = message in
        let ticket, tickets = Storage.pop_ticket ticket_id tickets in
        let ticket_send, ticket_keep = Ticket.split_ticket ticket amount in
        let receiver = RoutingInfo.get_receiver_l2_to_l1 routing_data in
        let ticket_transfer_op = match router with
        | Some router -> send_ticket_to_router ticket_send router receiver
        | None -> Ticket.send ticket_send receiver in
        let tickets = Big_map.update ticket_id (Some ticket_keep) tickets in
        let upd_store = { tickets; messages; next_message_id; metadata } in
        [ticket_transfer_op], upd_store
end
