(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)

#include "./ticket-type.mligo"

type withdrawals_key = {
  withdrawal_id : nat;
  // TODO: consider changing `full_amount` name
  full_amount : nat;
  target : address;
  timestamp : timestamp;
  // NOTE: the `payload` contains the `prepaid_amount` / `payment_amount`
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
  withdrawals : (withdrawals_key, address) big_map;
}

type withdrawal_entry = {
  withdrawal_id : nat;
  ticket : tez_ticket;
  timestamp : timestamp;
  base_withdrawer: address;
  payload: bytes;
  l2_caller: bytes;
}

type payout_entry = {
  withdrawal_id : nat;
  ticket : tez_ticket;
  target : address;
  timestamp : timestamp;
  service_provider : address;
  payload: bytes;
  l2_caller: bytes;
  full_amount : nat;
}

type return = operation list * storage

let assert_ticketer_is_expected (ticketer : address) (exchanger : address) : unit =
    if ticketer <> exchanger
    then failwith "Wrong ticketer"

[@entry]
let payout_withdrawal ({withdrawal_id; ticket; target; timestamp; service_provider; payload; l2_caller; full_amount} : payout_entry) (storage: storage) : return =
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
    failwith "The prepaid amount is not valid"
  else unit in
  let withdrawals_key = {withdrawal_id; full_amount; target; timestamp; payload; l2_caller} in
  let is_in_storage = Option.is_some (Big_map.find_opt withdrawals_key storage.withdrawals) in
  (* Ensure that the fast withdrawal was not already payed. *)
  if not is_in_storage then
    (* Update storage to record prepayment. *)
    let updated_withdrawals = Big_map.add withdrawals_key service_provider storage.withdrawals in
    let storage = { storage with withdrawals = updated_withdrawals } in
    (match Tezos.get_entrypoint_opt "%burn" storage.exchanger with
      | None -> failwith "Invalid tez ticket contract"
      | Some contract ->
        [Tezos.Next.Operation.transaction (target, ticket) 0mutez contract], storage)
  else
    failwith "The fast withdrawal was already payed"

[@entry]
let default ({ withdrawal_id; ticket; timestamp; base_withdrawer; payload; l2_caller} : withdrawal_entry)  (storage: storage) : return =
  // TODO: disallow xtz payments to this entrypoint (?)
  let is_sender_allowed = Tezos.get_sender () = storage.smart_rollup in
  let _ = if not is_sender_allowed then
    failwith "The sender is not allowed to call entrypoint"
  else unit in
  let (ticketer, (_payload, full_amount)), ticket = Tezos.Next.Ticket.read ticket in
  // TODO: consider checking ticket payload as well?
  let _ = assert_ticketer_is_expected ticketer storage.exchanger in
  let withdrawals_key = {withdrawal_id; full_amount; target=base_withdrawer; timestamp; payload; l2_caller} in
  match Big_map.find_opt withdrawals_key storage.withdrawals with
  | None ->
    (* No advance payment found, send to the withdrawer. *)
    (match Tezos.get_entrypoint_opt "%burn" storage.exchanger with
    | None -> failwith "Invalid tez ticket contract"
    | Some contract ->
      [Tezos.Next.Operation.transaction (base_withdrawer, ticket) 0mutez contract], storage)
  | Some payer ->
    (* If key found, then everything matches, the withdrawal was payed,
       we send the amount to the payer. *)
    let updated_withdrawals  = Big_map.remove withdrawals_key storage.withdrawals in
    let storage =  { storage with withdrawals = updated_withdrawals } in
    (match Tezos.get_entrypoint_opt "%burn" storage.exchanger with
    | None -> failwith "Invalid tez ticket contract"
    | Some contract ->
      [Tezos.Next.Operation.transaction (payer, ticket) 0mutez contract], storage)
