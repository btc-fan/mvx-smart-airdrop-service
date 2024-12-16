import json
import time

import requests

from config import DEFAULT_PROXY, rounds_per_epoch
from constants import *
from logger import logger


def get_status_of_tx(tx_hash: str) -> str:
    logger.info(f"Checking transaction status for hash: {tx_hash}")
    response = requests.get(f"{DEFAULT_PROXY}/transaction/{tx_hash}/process-status")
    response.raise_for_status()
    parsed = response.json()

    if "transaction not found" in response.text:
        return "expired"

    general_data = parsed.get("data")
    status = general_data.get("status")
    logger.info(f"Transaction status: {status} for tx_hash: {tx_hash}")
    return status


def send_egld_to_address(egld_amount, erd_address):
    logger.info(f"Sending {egld_amount} to address {erd_address}")
    details = {"address": f"{erd_address}", "balance": f"{egld_amount}"}

    details_list = [details]
    json_structure = json.dumps(details_list)
    response = requests.post(
        f"{DEFAULT_PROXY}/simulator/set-state", data=json_structure
    )
    response.raise_for_status()
    response_data = response.json()
    logger.info(
        f"Transfer response: {response_data.get('message', 'Balance updated successfully')}"
    )
    return response.text


def add_blocks(nr_of_blocks):
    logger.info(f"Requesting generation of {nr_of_blocks} blocks")
    response = requests.post(
        f"{DEFAULT_PROXY}/simulator/generate-blocks/{nr_of_blocks}"
    )
    response.raise_for_status()
    logger.info(
        f"Generated {nr_of_blocks} blocks; Response status: {response.status_code}"
    )
    return response.text


def get_block() -> int:
    response = requests.get(f"{DEFAULT_PROXY}/network/status/0")
    response.raise_for_status()
    parsed = response.json()

    general_data = parsed.get("data")
    general_status = general_data.get("status")
    nonce = general_status.get("erd_nonce")
    logger.info(f"Current block nonce: {nonce}")
    return nonce


def add_blocks_until_epoch_reached(epoch_to_be_reached: int):
    logger.info(f"Generating blocks until epoch {epoch_to_be_reached} is reached")
    req = requests.post(
        f"{DEFAULT_PROXY}/simulator/generate-blocks-until-epoch-reached/{str(epoch_to_be_reached)}"
    )
    req.raise_for_status()
    add_blocks(1)
    logger.info(f"Epoch {epoch_to_be_reached} reached")
    return req.text


def add_blocks_until_tx_fully_executed(tx_hash) -> str:
    logger.info(f"Checking status of transaction {tx_hash}")
    counter = 0

    while counter < MAX_NUM_OF_BLOCKS_UNTIL_TX_SHOULD_BE_EXECUTED:
        add_blocks(1)
        counter += 1

        time.sleep(WAIT_UNTIL_API_REQUEST_IN_SEC)
        tx_status = get_status_of_tx(tx_hash)
        if tx_status == "pending":
            logger.info(f"Transaction {tx_hash} still pending after {counter} blocks")
        else:
            logger.info(f"Transaction {tx_hash} executed after {counter} blocks")
            return tx_status
    raise Exception(
        f"Transaction {tx_hash} not executed within {MAX_NUM_OF_BLOCKS_UNTIL_TX_SHOULD_BE_EXECUTED} blocks."
    )


def is_chain_online() -> bool:
    while True:
        time.sleep(1)
        try:
            response = requests.get(f"{DEFAULT_PROXY}/network/status/0")
            response.raise_for_status()
            logger.info("Chain is online")
            return True
        except requests.exceptions.ConnectionError as e:
            logger.warning("Chain not started yet: ConnectionError")
        except Exception as e:
            logger.error(f"Unexpected error when checking chain status: {str(e)}")
            raise


def add_blocks_until_last_block_of_current_epoch() -> str:
    response = requests.get(f"{DEFAULT_PROXY}/network/status/4294967295")
    response.raise_for_status()
    parsed = response.json()

    general_data = parsed.get("data")
    status = general_data.get("status")
    passed_nonces = status.get("erd_nonces_passed_in_current_epoch")

    blocks_to_be_added = int(rounds_per_epoch) - passed_nonces
    logger.info(
        f"Adding {blocks_to_be_added} blocks to reach the end of the current epoch"
    )
    response_from_add_blocks = add_blocks(blocks_to_be_added)
    logger.info(f"Reached the last block of the current epoch")
    return response_from_add_blocks


def force_move_to_epoch(epoch_to_be_reached: int):
    """
    Forces the blockchain simulator to generate blocks until the specified epoch is reached.

    Args:
        epoch_to_be_reached (int): The target epoch to be reached.

    Returns:
        str: The response text from the server.
    """
    logger.info(f"Forcing epoch change until epoch {epoch_to_be_reached} is reached")

    # Get the current network status
    response = requests.get(f"{DEFAULT_PROXY}/network/status/0")
    response.raise_for_status()
    parsed = response.json()

    general_data = parsed.get("data")
    status = general_data.get("status")
    current_epoch = status.get("erd_epoch_number")

    # Check if the current epoch is less than the target epoch
    if current_epoch < epoch_to_be_reached:
        req = requests.post(
            f"{DEFAULT_PROXY}/simulator/force-epoch-change?targetEpoch={str(epoch_to_be_reached)}"
        )
        req.raise_for_status()  # Raise an error if the request fails
        logger.info(f"Epoch {epoch_to_be_reached} reached")
        return req.text
    else:
        logger.info(
            f"Current epoch {current_epoch} is already greater than or equal to {epoch_to_be_reached}."
        )
        return None
