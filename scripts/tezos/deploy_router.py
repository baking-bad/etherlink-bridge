from pytezos.client import PyTezosClient
from scripts.helpers.contracts.ticket_router_tester import TicketRouterTester


# TODO: consider making CLI for this function
def deploy_router(manager: PyTezosClient) -> TicketRouterTester:
    print('Deploying TicketRouterTester...')
    router_opg = TicketRouterTester.originate(manager).send()
    manager.wait(router_opg)
    return TicketRouterTester.from_opg(manager, router_opg)
