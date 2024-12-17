import time
from pathlib import Path

from multiversx_sdk import Transaction, TransactionsConverter, Token, TokenTransfer, TransferTransactionsFactory, \
    SmartContractTransactionsFactory, Address, UserPEM, UserSigner
from multiversx_sdk.abi import AddressValue, BigUIntValue

from python_files.config import CHAIN_ID, config, transaction_computer, provider
from python_files.constants import WALLETS_FOLDER, GAS_PRICE
from python_files.chain_commander import is_chain_online, force_move_to_epoch
from python_files.wallet import Wallet

factory = TransferTransactionsFactory(config)
sc_factory = SmartContractTransactionsFactory(config)
transaction_converter = TransactionsConverter()


# Initialize wallets
sender_wallet = Wallet(Path(WALLETS_FOLDER + "/sd_2_wallet_key_2.pem"))
receiver_wallet = Wallet(Path(WALLETS_FOLDER + "/sd_1_wallet_key_6.pem"))
relayer_wallet = Wallet(Path(WALLETS_FOLDER + "/sd_1_wallet_key_3.pem"))


def test_create_move_balance_transactions():

    TRANSFER_AMOUNT = 1  # 0.000000000000000001 xEGLD

    # Create 3 transfer transactions
    for i in range(3):
        transaction = Transaction(
            sender=sender_wallet.public_address(),
            receiver=receiver_wallet.public_address(),
            value=TRANSFER_AMOUNT,
            gas_limit=10000000,
            gas_price=GAS_PRICE,
            chain_id=CHAIN_ID,
        )
        transaction.nonce= sender_wallet.get_nonce_and_increment() + i

        tx_bytes = transaction_computer.compute_bytes_for_signing(transaction)
        transaction.signature = sender_wallet.get_signer().sign(tx_bytes)
        tx_hash = provider.send_transaction(transaction)

        print(f"Transaction hash: ", tx_hash)
        print(f"Transaction: ", transaction_converter.transaction_to_dictionary(transaction))

def test_create_move_balance_transactions_using_multi_transfer():
    addresses = ["erd1qjdmcps0ve7vst3cy0w5c426x4qrxg0unfzvcpqxke6hmp5d8huqw0u2h6", "erd1dyqtp8eldhvpc7v8qummq059jg2xrvweznstfr7wvc9rnpxd9tes82qy3s"]
    TRANSFER_AMOUNT = 1  # 0.000000000000000001 xEGLD
    service_address = "erd15uchpdmkn90qxd9add6npnst3mckkapkq7zmn5l8rlkwnvk7k0ese9q8z5"

    arguments = [AddressValue.from_address(Address.new_from_bech32(service_address))]
    for address in addresses:
        converted_address = AddressValue.from_address(Address.new_from_bech32(address))
        arguments.append(converted_address)
        arguments.append(BigUIntValue(TRANSFER_AMOUNT))


    first_token = Token("WEGLD-a28c59")
    first_transfer = TokenTransfer(first_token, TRANSFER_AMOUNT)

    second_token = Token("BUILDO-22c0a5")
    second_transfer = TokenTransfer(second_token, TRANSFER_AMOUNT*len(addresses))
    contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqf63uhw0jkqt3fy9u8n938hhz237ms0de4drq0rxpd2")

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

    tx_bytes = transaction_computer.compute_bytes_for_signing(transaction)
    transaction.signature = sender_wallet.get_signer().sign(tx_bytes)
    tx_hash = provider.send_transaction(transaction)

    print("Transaction hash: ",tx_hash)
    print("Transaction: ", transaction_converter.transaction_to_dictionary(transaction))
    print("Transaction data: ", transaction.data.decode())


def test_scenario_send_batch_transactions():
    """
    Test sending transactions from all addresses in the PEM file to a static receiver address.
    """
    tx_list = []

    # Create transactions for all sender addresses
    addresses = ["erd1qjdmcps0ve7vst3cy0w5c426x4qrxg0unfzvcpqxke6hmp5d8huqw0u2h6"]
    TRANSFER_AMOUNT = 1  # 0.000000000000000001 xEGLD
    service_address = "erd15uchpdmkn90qxd9add6npnst3mckkapkq7zmn5l8rlkwnvk7k0ese9q8z5"

    arguments = [AddressValue.from_address(Address.new_from_bech32(service_address))]

    # Repeat adding the address and amount 1500 times
    for _ in range(404):
        for address in addresses:
            converted_address = AddressValue.from_address(Address.new_from_bech32(address))
            arguments.append(converted_address)
            arguments.append(BigUIntValue(TRANSFER_AMOUNT))

    first_token = Token("WEGLD-a28c59")
    first_transfer = TokenTransfer(first_token, TRANSFER_AMOUNT)

    second_token = Token("BUILDO-22c0a5")
    second_transfer = TokenTransfer(second_token, TRANSFER_AMOUNT * 404)
    contract = Address.new_from_bech32("erd1qqqqqqqqqqqqqpgqf63uhw0jkqt3fy9u8n938hhz237ms0de4drq0rxpd2")

    transfers = [first_transfer, second_transfer]

    transaction = sc_factory.create_transaction_for_execute(
        sender=sender_wallet.get_address(),
        contract=contract,
        function="smartSave",
        gas_limit=600_000_000,
        arguments=arguments,
        token_transfers=transfers
    )

    transaction.nonce = sender_wallet.get_nonce_and_increment()

    tx_bytes = transaction_computer.compute_bytes_for_signing(transaction)
    transaction.signature = sender_wallet.get_signer().sign(tx_bytes)
    tx_hash = provider.send_transaction(transaction)

    print("Transaction hash: ", tx_hash)
    print("Transaction: ", transaction_converter.transaction_to_dictionary(transaction))
    print("Transaction data: ", transaction.data.decode())



