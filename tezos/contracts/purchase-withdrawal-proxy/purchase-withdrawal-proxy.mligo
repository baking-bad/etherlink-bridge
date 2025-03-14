(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
// TODO: add copyright

#import "../common/types/ticket.mligo" "Ticket"
#import "../common/entrypoints/purchase-withdrawal.mligo" "PurchaseWithdrawalEntry"

// TODO: consider reusing Withdrawal key and store it as a whole record in storage:
// TODO: consider renaming to PurchaseWithdrawalProxy entry? this is the same type
// TODO: is this order in sync with other types?
type storage = {
  withdrawal_id : nat;
  withdrawal_amount : nat;
  timestamp : timestamp;
  base_withdrawer : address;
  payload : bytes;
  l2_caller : bytes;
  service_provider : address;
  fast_withdrawal_contract: address;
  exchanger : address;
}

// TODO: move to storage.mligo OR purchase-withdrawal-entry.mligo
let to_purchase_withdrawal (ticket : Ticket.t) (store : storage) : PurchaseWithdrawalEntry.t =
  let {fast_withdrawal_contract = _; exchanger = _; withdrawal_id; base_withdrawer; timestamp; service_provider; payload; l2_caller; withdrawal_amount} = store in
  { withdrawal_id; ticket; base_withdrawer; timestamp; service_provider; payload; l2_caller; withdrawal_amount }

type return = operation list * storage


[@entry]
let purchase_withdrawal_proxy (params : storage) (_storage : storage) : return =
  let {fast_withdrawal_contract; exchanger; withdrawal_id; base_withdrawer; timestamp; service_provider; payload; l2_caller; withdrawal_amount} = params in
  if not (Bytes.length l2_caller = 20n) then
    failwith "L2 caller's address size should be 20 bytes long"
  else
  let amount = Tezos.get_amount () in
  let relay_entry = Tezos.address (Tezos.self("%relay_ticket"): Ticket.t contract) in
  match Tezos.get_entrypoint_opt "%mint" exchanger with
  | None -> failwith "Invalid tez ticket contract"
  | Some contract ->
    let mint = Tezos.Next.Operation.transaction relay_entry amount contract in
    let payout_storage = {fast_withdrawal_contract; exchanger; withdrawal_id; base_withdrawer; timestamp; service_provider; payload; l2_caller; withdrawal_amount} in
    [mint], payout_storage

[@entry]
let relay_ticket (ticket: Ticket.t) (store: storage) : return =
  let purchase_params = to_purchase_withdrawal ticket store in
  let purchase_op = PurchaseWithdrawalEntry.send store.fast_withdrawal_contract purchase_params in
  [purchase_op], store
