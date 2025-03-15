(*
    Key used in the FastWithdrawal contract ledger
*)
type t = {
    withdrawal_id : nat;
    full_amount : nat;
    timestamp : timestamp;
    base_withdrawer : address;
    payload : bytes;
    l2_caller : bytes;
}
