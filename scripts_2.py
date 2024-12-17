from pathlib import Path

from multiversx_sdk import TransactionsConverter, Token, TokenTransfer, TransferTransactionsFactory, \
    SmartContractTransactionsFactory, Address
from multiversx_sdk.abi import AddressValue, BigUIntValue

from python_files.config import CHAIN_ID, config, transaction_computer, provider
from python_files.constants import WALLETS_FOLDER, GAS_PRICE
from python_files.chain_commander import is_chain_online, force_move_to_epoch
from python_files.wallet import Wallet

factory = TransferTransactionsFactory(config)
sc_factory = SmartContractTransactionsFactory(config)
transaction_converter = TransactionsConverter()

sender_wallet = Wallet(Path(WALLETS_FOLDER + "/sd_1_wallet_key_1.pem"))
receiver_wallet = Wallet(Path(WALLETS_FOLDER + "/sd_1_wallet_key_6.pem"))
relayer_wallet = Wallet(Path(WALLETS_FOLDER + "/sd_1_wallet_key_3.pem"))

def create_move_balance_transaction_using_multi_transfer():
    addresses = [
        "erd1qjdmcps0ve7vst3cy0w5c426x4qrxg0unfzvcpqxke6hmp5d8huqw0u2h6",
        "erd1dyqtp8eldhvpc7v8qummq059jg2xrvweznstfr7wvc9rnpxd9tes82qy3s"
    ]
    amount = 1000000000000000  # Amount per transfer
    service_address = "erd15uchpdmkn90qxd9add6npnst3mckkapkq7zmn5l8rlkwnvk7k0ese9q8z5"
    arguments = []

    # Convert addresses and append arguments
    for address in addresses:
        converted_address = AddressValue.from_address(Address.new_from_bech32(address))
        arguments.append(converted_address)
        arguments.append(BigUIntValue(amount))

    # Token Transfers
    first_token = Token("WEGLD-a28c59")
    first_transfer = TokenTransfer(first_token, amount)

    second_token = Token("BUILDO-22c0a5")
    second_transfer = TokenTransfer(second_token, amount * len(addresses))

    # Smart Contract
    contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqf63uhw0jkqt3fy9u8n938hhz237ms0de4drq0rxpd2")

    # Create the transaction
    transfers = [first_transfer, second_transfer]
    transaction = sc_factory.create_transaction_for_execute(
        sender=sender_wallet.get_address(),
        contract=contract,
        function="smartSave",
        gas_limit=10000000,
        arguments=arguments,
        token_transfers=transfers
    )
    transaction.nonce = sender_wallet.get_nonce_and_increment()

    # Print transaction details
    print("Transaction:", transaction_converter.transaction_to_dictionary(transaction))
    print("Transaction data:", transaction.data.decode())

    # Optional: Uncomment to sign and send
    # tx_bytes = transaction_computer.compute_bytes_for_signing(transaction)
    # transaction.signature = sender_wallet.get_signer().sign(tx_bytes)
    # tx_hash = provider.send_transaction(transaction)
    # print(f"Transaction Hash: {tx_hash}")


if __name__ == "__main__":
    create_move_balance_transaction_using_multi_transfer()
