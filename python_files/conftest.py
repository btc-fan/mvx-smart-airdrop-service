from pathlib import Path

import pytest
from multiversx_sdk import SmartContractTransactionsFactory, Transaction
from multiversx_sdk.abi import Abi
from multiversx_sdk.core import Address

from config import address_computer, config, transaction_computer, provider
from constants import (
    CHAIN_SIMULATOR_FOLDER,
    SMART_CONTRACTS_FOLDER,
    WALLETS_FOLDER,
)
from chain_commander import force_move_to_epoch, is_chain_online, add_blocks_until_tx_fully_executed
from chain_simulator import ChainSimulator
from wallet import Wallet
from logger import logger


def send_transaction_and_check_for_success(transaction: Transaction) -> str:
    """
    Sends a single transaction and verifies its execution.

    Args:
        transaction (Transaction): The transaction to send.

    Returns:
        str: The hash of the successfully sent transaction.
    """
    tx_hash = provider.send_transaction(transaction)
    logger.info(f"Sent single transaction with hash: {tx_hash}")
    assert add_blocks_until_tx_fully_executed(tx_hash) == "success"
    return tx_hash

@pytest.fixture(scope="function")
def blockchain():
    chain_simulator = ChainSimulator(CHAIN_SIMULATOR_FOLDER)
    chain_simulator.start()
    yield chain_simulator
    chain_simulator.stop()


@pytest.fixture
def epoch(request):
    return request.param


@pytest.fixture(scope="function")
def deployed_smart_contract_address(blockchain):
    """
    Fixture to deploy a smart contract using MultiversX SDK with predefined settings.
    Returns the deployed contract address.
    """
    assert is_chain_online()

    CONTRACT_WASM = "answer.wasm"
    CONTRACT_ABI = "adder.abi.json"
    EGLD_AMOUNT = "1000000000000000000"  # 1 EGLD
    force_move_to_epoch(4)

    bytecode = (Path(SMART_CONTRACTS_FOLDER) / CONTRACT_WASM).read_bytes()
    abi = Abi.load(Path(SMART_CONTRACTS_FOLDER) / CONTRACT_ABI)
    sender_wallet = Wallet(Path(WALLETS_FOLDER + "/whale-internal-testnets.pem"))
    sender_address = sender_wallet.get_address()
    sender_wallet.set_balance(EGLD_AMOUNT)

    factory = SmartContractTransactionsFactory(config, abi)

    deploy_transaction = factory.create_transaction_for_deploy(
        sender=sender_address,
        bytecode=bytecode,
        gas_limit=100000000,
        arguments=[0],
        native_transfer_amount=0,
        is_upgradeable=True,
        is_payable=True,
        is_payable_by_sc=True,
        is_readable=True,
    )

    deploy_transaction.nonce = sender_wallet.get_nonce()
    signer_sender = sender_wallet.get_signer()
    deploy_transaction.signature = signer_sender.sign(
        transaction_computer.compute_hash_for_signing(deploy_transaction)
    )
    send_transaction_and_check_for_success(deploy_transaction)
    contract_address = address_computer.compute_contract_address(
        deployer=Address.new_from_bech32(deploy_transaction.sender),
        deployment_nonce=deploy_transaction.nonce,
    )
    logger.info(f"Deployed Smart Contract Address: {contract_address.to_bech32()}")
    return contract_address
