(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
// TODO: add copyright

#import "../common/entrypoints/settle-withdrawal.mligo" "SettleWithdrawalEntry"
#import "../common/types/ticket.mligo" "Ticket"

// TODO: create module to manage withdrawals bigmap
type withdrawal = {
  withdrawal_id : nat;
  withdrawal_amount : nat;
  base_withdrawer : address;
  timestamp : timestamp;
  payload: bytes;
  l2_caller: bytes;
}

(*
  Fast Withdrawal contract storage:
  - exchanger: the address of the ticketer
  - smart_rollup: the address of the Etherlink smart rollup
  - withdrawals: stores service_provider for each withdrawal key
*)
type storage = {
  exchanger: address;
  smart_rollup : address;
  withdrawals : (withdrawal, address) big_map;
}

// TODO: move to separate file:
type purchase_withdrawal_entry = {
  withdrawal_id : nat;
  ticket : Ticket.t;
  base_withdrawer : address;
  timestamp : timestamp;
  service_provider : address;
  payload: bytes;
  l2_caller: bytes;
  withdrawal_amount : nat;
}

type return = operation list * storage

let assert_ticketer_is_expected (ticketer : address) (exchanger : address) : unit =
    if ticketer <> exchanger
    then failwith "Wrong ticketer"

[@entry]
let purchase_withdrawal ({withdrawal_id; ticket; base_withdrawer; timestamp; service_provider; payload; l2_caller; withdrawal_amount} : purchase_withdrawal_entry) (storage: storage) : return =
  // TODO: consider changing entrypoint name
  // TODO: disallow xtz payments to this entrypoint
  let (ticketer, (_, prepaid_amount)), ticket = Tezos.Next.Ticket.read ticket in
  // TODO: consider checking ticket payload as well?
  let _ = assert_ticketer_is_expected ticketer storage.exchanger in
  // TODO: consider converting to bytes without packing?
  let prepaid_amount_bytes = Bytes.pack prepaid_amount in
  // TODO: move asserts into separate functions
  let is_valid_prepaid_amount = prepaid_amount_bytes = payload in
  let _ = if not is_valid_prepaid_amount then
    failwith "Invalid purchase amount."
  else unit in
  let withdrawal = {withdrawal_id; withdrawal_amount; base_withdrawer; timestamp; payload; l2_caller} in
  let is_in_storage = Option.is_some (Big_map.find_opt withdrawal storage.withdrawals) in
  (* Ensure that the fast withdrawal was not already payed. *)
  if not is_in_storage then
    (* Update storage to record prepayment. *)
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
  let is_sender_allowed = Tezos.get_sender () = storage.smart_rollup in
  let _ = if not is_sender_allowed then
    failwith "Sender is not allowed to call this entrypoint"
  else unit in
  let (ticketer, (_payload, withdrawal_amount)), ticket = Tezos.Next.Ticket.read ticket in
  // TODO: consider checking ticket payload as well?
  let _ = assert_ticketer_is_expected ticketer storage.exchanger in
  let withdrawal = {withdrawal_id; withdrawal_amount; base_withdrawer; timestamp; payload; l2_caller} in
  match Big_map.find_opt withdrawal storage.withdrawals with
  | None ->
    (* No advance payment found, send to the withdrawer. *)
    (match Tezos.get_entrypoint_opt "%burn" storage.exchanger with
    | None -> failwith "Invalid tez ticket contract"
    | Some contract ->
      [Tezos.Next.Operation.transaction (base_withdrawer, ticket) 0mutez contract], storage)
  | Some payer ->
    (* If key found, then everything matches, the withdrawal was payed,
       we send the amount to the payer. *)
    let updated_withdrawals  = Big_map.remove withdrawal storage.withdrawals in
    let storage =  { storage with withdrawals = updated_withdrawals } in
    (match Tezos.get_entrypoint_opt "%burn" storage.exchanger with
    | None -> failwith "Invalid tez ticket contract"
    | Some contract ->
      [Tezos.Next.Operation.transaction (payer, ticket) 0mutez contract], storage)
