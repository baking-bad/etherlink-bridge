(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
// TODO: add copyright

#import "../common/entrypoints/settle-withdrawal.mligo" "SettleWithdrawalEntry"
#import "../common/entrypoints/purchase-withdrawal.mligo" "PurchaseWithdrawalEntry"
#import "../common/entrypoints/exchanger-burn.mligo" "ExchangerBurnEntry"
#import "../common/types/ticket.mligo" "Ticket"
#import "../common/types/fast-withdrawal.mligo" "FastWithdrawal"

(*
    Fast Withdrawal contract storage:
    - exchanger: the address of the ticketer
    - smart_rollup: the address of the Etherlink smart rollup
    - withdrawals: stores service_provider for each withdrawal key
*)
type storage = {
    exchanger: address;
    smart_rollup : address;
    // TODO: move withdrawals management functions to separate file
    withdrawals : (FastWithdrawal.t, address) big_map;
}

type return = operation list * storage

[@inline]
let assert_ticketer_is_expected (ticketer : address) (exchanger : address) : unit =
    if ticketer <> exchanger
    then failwith "Wrong ticketer"

[@inline]
let assert_sender_is_allowed (smart_rollup : address) : unit =
    if Tezos.get_sender () <> smart_rollup
    then failwith "Sender is not allowed to call this entrypoint"

[@entry]
let purchase_withdrawal ({withdrawal_id; ticket; base_withdrawer; timestamp; service_provider; payload; l2_caller; withdrawal_amount} : PurchaseWithdrawalEntry.t) (storage: storage) : return =
    // TODO: disallow xtz payments to this entrypoint
    let (ticketer, (_, prepaid_amount)), ticket = Tezos.Next.Ticket.read ticket in
    // TODO: consider checking ticket payload as well?
    let _ = assert_ticketer_is_expected ticketer storage.exchanger in
    // TODO: consider converting to bytes without packing?
    let prepaid_amount_bytes = Bytes.pack prepaid_amount in

    // TODO: check if timestamp expired and if it is, then valid amount should equal withdrawal_amount
    // TODO: move asserts into separate functions
    let is_valid_prepaid_amount = prepaid_amount_bytes = payload in
    let _ = if not is_valid_prepaid_amount then
        failwith "Invalid purchase amount."
    else unit in
    // TODO: PurchaseWithdrawalEntry.to_key ?
    let withdrawal = {withdrawal_id; withdrawal_amount; base_withdrawer; timestamp; payload; l2_caller} in

    // TODO: Storage.get withdrawal storage ?
    let is_in_storage = Option.is_some (Big_map.find_opt withdrawal storage.withdrawals) in
    (* Ensure that the fast withdrawal was not already payed. *)
    if not is_in_storage then
        (* Update storage to record prepayment. *)
        // TODO: Storage.add withdrawal storage ?
        let updated_withdrawals = Big_map.add withdrawal service_provider storage.withdrawals in
        let storage = { storage with withdrawals = updated_withdrawals } in
        (match Tezos.get_entrypoint_opt "%burn" storage.exchanger with
          | None -> failwith "Invalid tez ticket contract"
          | Some contract ->
              [Tezos.Next.Operation.transaction (base_withdrawer, ticket) 0mutez contract], storage)
    else
        failwith "The fast withdrawal was already payed"

[@entry]
let default ({ withdrawal_id; ticket; timestamp; base_withdrawer; payload; l2_caller} : SettleWithdrawalEntry.t)  (storage: storage) : return =
    // TODO: disallow xtz payments to this entrypoint (?)
    let (ticketer, (_payload, withdrawal_amount)), ticket = Tezos.Next.Ticket.read ticket in
    let _ = assert_sender_is_allowed storage.smart_rollup in
    let _ = assert_ticketer_is_expected ticketer storage.exchanger in
    // TODO: consider checking ticket payload as well?
    // TODO: SettleWithdrawalEntry.to_key ?
    let withdrawal = {withdrawal_id; withdrawal_amount; base_withdrawer; timestamp; payload; l2_caller} in
    // TODO: Storage.get withdrawal storage ?
    match Big_map.find_opt withdrawal storage.withdrawals with
    | None ->
        (* No advance payment found, send to the withdrawer. *)
        let ticket_burn_op = ExchangerBurnEntry.send storage.exchanger (base_withdrawer, ticket) in
        [ticket_burn_op], storage
    | Some payer ->
        (* If key found, then everything matches, the withdrawal was payed,
           we send the amount to the payer. *)
        let updated_withdrawals  = Big_map.remove withdrawal storage.withdrawals in
        let storage = { storage with withdrawals = updated_withdrawals } in
        let ticket_burn_op = ExchangerBurnEntry.send storage.exchanger (payer, ticket) in
        [ticket_burn_op], storage
