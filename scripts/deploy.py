from pytezos import pytezos
from getpass import getpass
from dotenv import load_dotenv
import os


load_dotenv()
RPC_SHELL = os.getenv('RPC_SHELL') or 'https://rpc.tzkt.io/nairobinet/'
PRIVATE_KEY = os.getenv('PRIVATE_KEY') or getpass('Enter private key: ')

client = pytezos.using(shell=RPC_SHELL, key=PRIVATE_KEY)
# TODO: reveal key if needed: client.reveal().send()
# TODO: make deploy function
raise(Exception('Not implemented'))


# TODO: main function:
'''
def main():
    ...

if __name__ == '__main__':
    main()
'''
