#import "../common/types/routing-info.mligo" "RoutingInfo"
#import "../common/entrypoints/rollup-deposit.mligo" "RollupDepositEntry"
#import "../common/entrypoints/router-withdraw.mligo" "RouterWithdrawEntry"
#import "../common/entrypoints/ticketer-deposit.mligo" "TicketerDepositEntry"
#import "../common/types/ticket.mligo" "Ticket"


module TicketRouterTester = struct
    (*
        TicketRouterTester is a helper contract that helps developers test
        Etherlink Bridge ticket layer protocol components. It provides
        a simple interface to mint, deposit and withdraw tickets to and from
        Etherlink Bridge.

        There is the `set` entrypoint which allows to configure how tickets
        will be handled after `mint`, `default` and `withdraw` calls. Three
        options are available:
        - `default` which allows to redirect/mint ticket to the
            implicit address
        - `routerWithdraw` which allows to redirect/mint ticket to the ticketer
            `withdraw` entrypoint
        - `rollupDeposit` which allows to redirect/mint ticket to the
            rollup `deposit` entrypoint

        Also, there are:
        - two entrypoints allow receiving tickets from other contracts:
            - `default` handles tickets in the same way implicit address would do
            - `withdraw` handles tickets in the same way Ticketer would do
        - `mint` entry allows minting new tickets during `intrernal_call`.

        Finally, there is a `deposit` entrypoint which allows to use
        TicketRouterTester as a Ticketer mock contract. The call to this
        entrypoint does not have any effect.

        This contract is expected to be used only for testing purposes.
    *)

    type entrypoint_t =
        | Default of unit
        | RouterWithdraw of address
        | RollupDeposit of RoutingInfo.l1_to_l2_t

    type internal_call_t = [@layout:comb] {
        target : address;
        entrypoint : entrypoint_t;
        xtz_amount : tez;
    }

    type storage_t = [@layout:comb] {
        internal_call : internal_call_t;
        metadata : (string, bytes) big_map;
    }

    type mint_params_t = [@layout:comb] {
        content : Ticket.content_t;
        amount : nat;
    }

    type return_t = operation list * storage_t

    [@entry] let set
            (internal_call : internal_call_t)
            (store : storage_t) : return_t =
        [], { store with internal_call }

    let make_operation
            (ticket : Ticket.t)
            (internal_call : internal_call_t) : operation =
        (*
            `make_operation` wraps a ticket into the appropriate entrypoint
            structure and calls the target contract with the ticket.
        *)
        let { target; entrypoint; xtz_amount } = internal_call in
        match entrypoint with
        | Default () ->
            let entry = Ticket.get target in
            Tezos.transaction ticket xtz_amount entry
        | RouterWithdraw (receiver) ->
            let withdraw = { receiver; ticket } in
            let entry = RouterWithdrawEntry.get target in
            Tezos.transaction withdraw xtz_amount entry
        | RollupDeposit (routing_info) ->
            let deposit = { routing_info; ticket } in
            let deposit_wrap = RollupDepositEntry.wrap deposit in
            let entry = RollupDepositEntry.get target in
            Tezos.transaction deposit_wrap xtz_amount entry

    [@entry] let default
            (ticket : Ticket.t)
            (store : storage_t) : return_t =
        (*
            `default` entrypoint is used to receive tickets in the same way
            an implicit address would do.

            @param ticket: a ticket to be received
        *)
        [make_operation ticket store.internal_call], store

    [@entry] let withdraw
            (params : RouterWithdrawEntry.t)
            (store : storage_t) : return_t =
        (*
            `withdraw` entrypoint is used to receive tickets in the same way
            Ticketer and any other contract that implements the Router
            withdraw interface would do.

            @param receiver: an address that will receive the unlocked token.
                NOTE: the target from `store.internal_call` will be ignored.
            @param ticket: provided ticket to be burned.
        *)
        let { ticket; receiver } = params in
        let internal_call = { store.internal_call with target = receiver } in
        [make_operation ticket internal_call], store

    [@entry] let mint
            (params : mint_params_t)
            (store : storage_t) : return_t =
        (*
            `mint` entrypoint is used to mint new tickets during the
            `internal_call`.

            @param content: any ticket content
            @param amount: ticket amount
        *)
        let { content; amount } = params in
        let ticket = Ticket.create content amount in
        [make_operation ticket store.internal_call], store

    [@entry] let deposit
            (_params : TicketerDepositEntry.t)
            (store : storage_t) : return_t =
        (*
            `deposit` entrypoint is used to pretend to be a Ticketer contract
            for testing purposes as a mock contract.
            The call to the `deposit` entrypoint does not have any effect.

            @param amount: ticketer deposit parameters that are not used
        *)
        [], store
end
