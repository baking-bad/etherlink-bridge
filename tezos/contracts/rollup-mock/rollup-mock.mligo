#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/entrypoints/rollup-deposit.mligo" "RollupDepositEntry"
#import "./tickets.mligo" "Tickets"


module RollupMock = struct
    (*
        RollupMock is helper contract used to deposit and release tickets on
        the L1 side in the similar way Rollup would do.
    *)

    type storage_t = {
        tickets : Tickets.t;
        metadata : (string, bytes) big_map;
    }

    type execute_params_t = {
        ticket_id : Tickets.id_t;
        amount : nat;
        receiver : address;
        router : address;
    }

    type return_t = operation list * storage_t

    [@entry] let rollup
            (rollup_entry : RollupDepositEntry.t)
            (store : storage_t)
            : return_t =
        (*
            `rollup` entrypoint emulates L1 rollup full entrypoint.
            It allows to deposit tickets the same way as L1 rollup would do.
            RollupMock saves provided tickets in the storage.
        *)

        let deposit = RollupDepositEntry.unwrap rollup_entry in
        let { ticket; routing_info = _r } = deposit in
        let { tickets; metadata } = store in
        let tickets = Tickets.save ticket tickets in
        let store = { tickets; metadata } in
        [], store

    [@entry] let execute_outbox_message
            (params : execute_params_t)
            (store : storage_t)
            : return_t =
        (*
            `execute_outbox_message` allows to release tickets the same way
            as L1 rollup would do when someone triggered L1 outbox message
            execution. It will call the withdraw router contract with the
            ticket and receiver address.

            NOTE: the entrypoint for the real L1 rollup has different
            signature: `commitment` and `proof` should be provided instead
            execution parameters as in this mock.
        *)

        let { tickets; metadata } = store in
        let { ticket_id; router; amount; receiver } = params in
        let ticket, tickets = Tickets.get ticket_id amount tickets in
        let withdraw_params = { ticket; receiver } in
        let withdraw_op = RouterWithdrawEntry.send router withdraw_params in
        let store = { tickets; metadata } in
        [withdraw_op], store
end
