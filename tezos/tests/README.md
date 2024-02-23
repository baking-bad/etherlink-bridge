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

- [ ] test_create_and_burn_multuple_tickets_from_different_users
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
- [ ] test_should_fail_to_unpack_ticket_minted_by_another_ticketer
- [ ] test_should_fail_to_unpack_ticket_with_incorrect_content
    - this one is probably imposible to test, need to send fake ticket
- [ ] test_should_fail_on_deposit_with_attached_xtz
- [ ] test_should_fail_on_withdraw_with_attached_xtz
- [ ] test_should_increase_total_supply
- [ ] test_should_decrease_total_supply
- [ ] test_should_return_content_on_view_call
- [ ] test_should_return_token_on_view_call
- [x] test_should_not_allow_to_mint_new_ticket_if_total_supply_exceeds_max
- [-] test_should_not_allow_to_burn_ticket_if_total_supply_goes_negative
    - this one is impossible to test because it requires minting new tickets without updating `total_supply`

## Utils tests [(code)](test_utils.py):
- [ ] test_ticket_content_generation_for_empty_metadata
- [ ] test_ticket_content_generation_for_fa2_without_extra_metadata
- [ ] test_ticket_content_generation_for_fa12_without_extra_metadata
- [ ] test_ticket_content_generation_with_extra_metadata_added

## TicketHelper tests [(code)](test_ticket_helper.py):
- [ ] test_deposit_succeed_for_correct_fa2_token_and_ticketer
    - should send ticket to rollup
- [ ] test_deposit_succeed_for_correct_fa12_token_and_ticketer
    - should send ticket to rollup
- [ ] test_context_updated_during_deposit
    - probably will require some mock ticketer (?)
- [ ] test_can_receive_ticket_when_context_set
- [ ] test_should_not_accept_ticket_when_context_empty
- [ ] test_should_not_accept_ticket_from_wrong_ticketer
- [ ] test_should_fail_on_deposit_with_attached_xtz
- [ ] test_should_fail_on_unwrap_with_attached_xtz
- [ ] test_should_fail_when_received_ticket_along_with_xtz
- [x] test_should_prepare_correct_routing_info
- [ ] test_should_fail_if_routing_info_has_inccorrect_size (?)
