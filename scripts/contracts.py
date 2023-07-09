from os.path import dirname
from os.path import join
from pytezos.contract.interface import ContractInterface


class Contract:
    build_dir: str = join(dirname(__file__), '..', 'build')
    name: str
    filename: str
    contract: ContractInterface

    def __init__(self, name: str):
        self.name = name
        self.filename = join(self.build_dir, name + '.tz')
        self.contract = ContractInterface.from_file(self.filename)


TICKETER = Contract('ticketer')
PROXY = Contract('proxy')
LOCKER = Contract('locker')
