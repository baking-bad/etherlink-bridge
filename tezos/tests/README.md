# Sandbox test cases list:

## Sandbox integration test [(code)](test_communication.py)
- [x] test_should_be_able_to_deposit_and_withdraw
    - check alice converts 100 tokens to tickets and deposits it to rollup
    - check rollup has 100 tickets
    - check ticketer has 100 tokens
    - check alice has 0 tickets
    - check boris withdraws 5 tickets from rollup
    - check rollup has 95 tickets
    - check boris has 5 tokens

- [x] test_create_and_burn_multuple_tickets_from_different_users
    - check alice create one ticket from 5 tokens
    - check alice burns 2 tickets
    - check alice transfers 2 tickets to boris
    - check boris creates 1 more ticket
    - check boris burns 3 tickets

## Ticketer tests [(code)](test_ticketer.py):
- [x] test_create_ticket_on_deposit_fa12_if_token_expected
    - check ticket minted for sender
    - check ticket payload is expected
    - check that tokens locked on ticketer contract
- [x] test_create_ticket_on_deposit_fa2_if_token_expected
    - check ticket minted for sender
    - check ticket payload is expected
    - check that tokens locked on ticketer contract
- [x] test_should_send_fa2_to_receiver_on_withdraw_if_ticket_correct
    - check receiver get token
    - check ticket burned
- [x] test_should_send_fa12_to_receiver_on_withdraw_if_ticket_correct
    - check receiver get token
    - check ticket burned
- [x] test_should_fail_to_unpack_ticket_minted_by_another_ticketer
- [x] test_should_fail_to_unpack_ticket_with_incorrect_content
- [x] test_should_fail_on_deposit_with_attached_xtz
- [x] test_should_fail_on_withdraw_with_attached_xtz
- [x] test_should_increase_total_supply
- [x] test_should_decrease_total_supply
- [x] test_create_ticket_on_deposit_fa2_with_non_zero_id
- [x] test_should_return_content_on_view_call_for_fa12
- [x] test_should_return_content_on_view_call_for_fa2
- [x] test_should_return_token_on_view_call_for_fa12
- [x] test_should_return_token_on_view_call_for_fa2
- [x] test_should_not_allow_to_mint_new_ticket_if_total_supply_exceeds_max
- [-] test_should_not_allow_to_burn_ticket_if_total_supply_goes_negative
    - this one is impossible to test because it requires minting new tickets without updating `total_supply`

## Utils tests [(code)](test_utils.py):
- [x] test_ticket_content_generation_for_empty_metadata
- [x] test_ticket_content_generation_for_fa2_without_extra_metadata
- [x] test_ticket_content_generation_for_fa12_without_extra_metadata
- [x] test_ticket_content_generation_with_extra_metadata_added

## TokenBridgeHelper tests [(code)](test_token_bridge_helper.py):
- [x] test_deposit_succeed_for_correct_fa2_token_and_ticketer
    - should send ticket to rollup
- [x] test_deposit_succeed_for_correct_fa12_token_and_ticketer
    - should send ticket to rollup
- [x] test_context_updated_during_deposit
    - use TicketRouterTester as a mock instead of Ticketer
    - check context updated correctly before ticket received
    - check can receive ticket when context set
    - check context emptied after ticket received
- [x] test_should_not_accept_ticket_when_context_empty
- [x] test_should_not_accept_ticket_from_wrong_sender
- [x] test_should_fail_on_deposit_with_attached_xtz
- [x] test_should_fail_on_unwrap_with_attached_xtz
- [x] test_should_fail_when_received_ticket_along_with_xtz
- [x] test_should_prepare_correct_routing_info
- [x] test_should_fail_if_routing_info_has_inccorrect_size
- [x] test_should_redirect_ticket_to_the_ticketer_on_withdraw
    - check ticket will be redirected to the ticketer in the storage
    - check ticket will be redirected to the ticketer even its address differs from the stored ticketer address

## FastWithdrawal tests [(code)](test_fast_withdrawal.py):
- [x] test_should_create_withdrawal_record_after_xtz_withdrawal_purchased
    - check key is added to `withdrawals` big_map
    - check ticketer content is `(0, None)`

- [x] test_should_accept_different_payloads_for_different_ticket_amounts
    - check key is added for ticket amount = `1`
    - check key is added for ticket amount = `17`
    - check key is added for ticket amount = `1_000_000_000_000`

- [x] test_should_create_different_withdrawal_records
    - check new key is added for transaction with different `timestamp`
    - check new key is added for transaction with different `base_withdrawer`
    - check new key is added for transaction with different `payload` and ticket amount
    - check new key is added for transaction with different `l2_caller`

- [x] test_should_reject_duplicate_withdrawal
    - check rejection when initiated by the same provider
    - check rejection when initiated by a different provider
    - check rejection if the withdrawal was already finalized

- [x] test_provider_receives_xtz_withdrawal_after_purchase
    - check provider balance increases by full withdrawal amount
    - check withdrawal status is `Cemented` after payout

- [x] test_user_receives_xtz_withdrawal_when_no_purchase_made
    - check user balance increases by full withdrawal amount

- [x] test_should_reject_xtz_withdrawal_purchase_with_wrong_xtz_amount
    - check transaction rejected if provided xtz amount is not equal amount in payout (and withdrawal is not expired yet)

- [x] test_should_reject_settlement_with_attached_xtz
- [x] test_should_reject_settlement_from_wrong_rollup_address

- [x] test_should_pay_custom_provider_when_specified
    - check specified alternative provider receives withdrawal payout
    - check withdrawal status is `Cemented` after payout
    - check for XTZ, FA1.2 and FA2

- [x] test_should_allow_xtz_withdrawal_purchase_at_full_price_after_timestamp_expired

- [x] test_rejects_xtz_withdrawal_purchase_at_discounted_price_if_expired

- [x] test_rejects_xtz_withdrawal_purchase_with_wrong_ticket_content
    - check `token_id` wrong
    - check `payload` is Some(bytes)
- [x] test_rejects_future_timestamp
- [x] test_should_return_config_on_get_config_view

- [x] test_should_emit_events_on_payout_withdrawal_and_finalization
    - check that `payout_withdrawal` emits the correct event
    - check that `default` (finalization) emits the correct event for a paid withdrawal
    - check that `default` (finalization) emits the correct event for an unpaid withdrawal

- [x] test_rejects_invalid_payload
- [x] test_rejects_if_l2_caller_is_not_20_bytes_long
- [x] test_non_native_tickets_not_supported_for_payout
- [x] test_non_xtz_tickets_redirected_on_settlement
- [x] test_reject_cemented_withdrawal
- [x] test_reject_if_payout_exceeds_full_amount
