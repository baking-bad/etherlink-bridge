(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
// TODO: add copyright

#import "../common/types/ticket.mligo" "Ticket"
#import "../common/entrypoints/purchase-withdrawal.mligo" "PurchaseWithdrawalEntry"
#import "../common/entrypoints/exchanger-mint.mligo" "ExchangerMintEntry"
#import "./purchase-params.mligo" "PurchaseParams"


type storage = PurchaseParams.t
type return = operation list * storage

[@inline]
let assert_l2_caller_length_20n (l2_caller : bytes) : unit =
    if Bytes.length l2_caller <> 20n then
        failwith "L2 caller's address size should be 20 bytes long"

// TODO: consider renaming to just `purchase`?
[@entry]
let purchase_withdrawal_proxy
        (params : PurchaseParams.t)
        (_storage : storage) : return =
    (* TODO: add docstring *)

    let _ = assert_l2_caller_length_20n params.withdrawal.l2_caller in

    let amount = Tezos.get_amount () in
    let relay_entry = Tezos.address (Tezos.self ("%relay_ticket") : Ticket.t contract) in
    let mint_op = ExchangerMintEntry.send params.exchanger amount relay_entry in
    let new_storage = params in
    [mint_op], new_storage

[@entry]
let relay_ticket
        (ticket: Ticket.t)
        (store: storage) : return =
    (* TODO: add docstring *)

    let purchase_params = PurchaseParams.to_purchase_withdrawal ticket store in
    let purchase_op = PurchaseWithdrawalEntry.send store.fast_withdrawal_contract purchase_params in
    [purchase_op], store
