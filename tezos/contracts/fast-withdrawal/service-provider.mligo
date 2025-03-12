(* SPDX-CopyrightText 2025 Functori <contact@functori.com> *)
(* SPDX-CopyrightText 2025 Nomadic Labs <contact@nomadic-labs.com> *)
// TODO: add copyright

// TODO: reuse existing types
#include "./ticket-type.mligo"

// TODO: consider moving this contract to separate directory
// TODO: consider renaming contract to the FastWithdrawalHelper? FastWithdrawalProxy?

type storage = {
  fast_withdrawal_contract: address;
  exchanger : address;
  withdrawal_id : nat;
  base_withdrawer : address;
  timestamp : timestamp;
  service_provider : address;
  payload : bytes;
  l2_caller : bytes;
  full_amount : nat;
}

type purchase_withdrawal_proxy_entry = {
  fast_withdrawal_contract: address;
  exchanger : address;
  withdrawal_id : nat;
  base_withdrawer : address;
  timestamp : timestamp;
  service_provider : address;
  payload: bytes;
  l2_caller : bytes;
  full_amount : nat;
}

type return = operation list * storage


[@entry]
let purchase_withdrawal_proxy ({fast_withdrawal_contract; exchanger; withdrawal_id; base_withdrawer; timestamp; service_provider; payload; l2_caller; full_amount} : purchase_withdrawal_proxy_entry) (_storage: storage) : return =
  if not (Bytes.length l2_caller = 20n) then
    failwith "L2 caller's address size should be 20 bytes long"
  else
  let amount = Tezos.get_amount () in
  let relay_entry = Tezos.address (Tezos.self("%relay_ticket"): tez_ticket contract) in
  match Tezos.get_entrypoint_opt "%mint" exchanger with
  | None -> failwith "Invalid tez ticket contract"
  | Some contract ->
    let mint = Tezos.Next.Operation.transaction relay_entry amount contract in
    let payout_storage = {fast_withdrawal_contract; exchanger; withdrawal_id; base_withdrawer; timestamp; service_provider; payload; l2_caller; full_amount} in
    [mint], payout_storage

[@entry]
let relay_ticket (ticket: tez_ticket) ({fast_withdrawal_contract; exchanger; withdrawal_id; base_withdrawer; timestamp; service_provider; payload; l2_caller; full_amount}: storage) : return =
  match Tezos.get_entrypoint_opt "%purchase_withdrawal" fast_withdrawal_contract with
  | None -> failwith "Invalid entrypoint"
  | Some contract ->
      // TODO: this type is shared between Service Provider and Fast Withdrawal, need
      //       to move it to some common space:
      let full_payload = (withdrawal_id, (ticket, (base_withdrawer, (timestamp, (service_provider, (payload, (l2_caller, full_amount))))))) in
      [Tezos.Next.Operation.transaction full_payload 0mutez contract], {fast_withdrawal_contract; exchanger; withdrawal_id; base_withdrawer; timestamp; service_provider; payload; l2_caller; full_amount}
