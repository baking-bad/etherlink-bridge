#import "../common/tokens/index.mligo" "Token"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/entrypoints.mligo" "Entrypoints"
#import "../common/errors.mligo" "Errors"
#import "../common/utility.mligo" "Utility"
#import "./storage.mligo" "Storage"


module Ticketer = struct

    (*
        Ticketer is a contract that allows to convert any legacy FA1.2 or
        FA2 token to a ticket. The legacy token can be later released by the
        ticket holder.

        Information about FA2 and FA1.2 tokens added to the ticket payload.
        It is assumed that the ticker will also be able to add additional
        metadata for different types of tokens, if this metadata is added
        to the ticker during origination. (TODO: add this functionality)
    *)

    type return_t = operation list * Storage.t

    [@entry] let deposit
            (params : Entrypoints.deposit_params)
            (store : Storage.t) : return_t =
        // TODO: decide: should we limit Token.contract_address that allowed to be
        //       converted to ticket? (it is easier to start with the most general
        //       case, so the answer is "no" for now)
        let () = Utility.assert_no_xtz_deposit () in
        let { token; amount } = params in
        let new_store, token_id = Storage.get_or_create_token_id token store in
        let token_info = Token.make_token_info token in
        let token_info_extra : Token.token_info_t =
            match Map.find_opt token store.extra_metadata with
            | None -> token_info
            | Some extra_metadata ->
                Token.merge_token_info token_info extra_metadata in
        let payload = {
            token_id = token_id;
            metadata = Some (Bytes.pack token_info_extra);
        } in
        let ticket = Ticket.create payload amount in
        let sender = Tezos.get_sender () in
        let sender_contract = Ticket.get_ticket_entrypoint sender in
        let self = Tezos.get_self_address () in
        let token_transfer_op = Token.get_transfer_op token amount sender self in
        let ticket_transfer_op = Tezos.transaction ticket 0mutez sender_contract in
        [token_transfer_op; ticket_transfer_op], new_store

    [@entry] let withdraw
            (params : Entrypoints.withdraw_params)
            (store : Storage.t)
            : return_t =
        let { ticket; receiver } = params in
        let (ticketer, (payload, amount)), _ = Tezos.read_ticket ticket in
        let () = Utility.assert_address_is_self ticketer in
        let () = Utility.assert_no_xtz_deposit () in
        let token = Storage.get_token payload.token_id store in
        let self = Tezos.get_self_address () in
        let transfer_op = Token.get_transfer_op token amount self receiver in
        [transfer_op], store
end
