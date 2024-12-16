# utils/chain_simulator.py

import json
import os
import re
import signal
import subprocess
import threading
import time
from pathlib import Path
from queue import Queue

from config import (
    log_level,
    num_validators_meta,
    num_validators_per_shard,
    num_waiting_validators_meta,
    num_waiting_validators_per_shard,
    rounds_per_epoch,
)
from constants import CHAIN_SIMULATOR_FOLDER
from logger import logger


class ChainSimulator:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.log_level = log_level
        self.num_validators_per_shard = num_validators_per_shard
        self.num_validators_meta = num_validators_meta
        self.num_waiting_validators_per_shard = num_waiting_validators_per_shard
        self.num_waiting_validators_meta = num_waiting_validators_meta
        self.rounds_per_epoch = rounds_per_epoch
        self.process = None
        self.logs = Queue()
        self.all_logs = []  # Store all logs here
        logger.info(
            f"Trying to Initialize ChainSimulator with configuration at {path}\n"
        )

        # Check if the ChainSimulator binary exists in the specified path
        if not os.path.exists(CHAIN_SIMULATOR_FOLDER + "/chainsimulator"):
            logger.error("ChainSimulator binary not found at the specified path.")
            raise FileNotFoundError(
                "ChainSimulator binary not found at the specified path."
            )

    def start(self):
        command = f"./chainsimulator --rounds-per-epoch {self.rounds_per_epoch} \
                    -num-validators-per-shard {self.num_validators_per_shard} \
                    -num-waiting-validators-per-shard {self.num_waiting_validators_per_shard} \
                    -num-validators-meta {self.num_validators_meta} \
                    -num-waiting-validators-meta {self.num_waiting_validators_meta} \
                    --log-level '*:DEBUG,txcache:TRACE'"
        command = " ".join(command.split())

        logger.info(f"Starting ChainSimulator with command: {command}")

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            preexec_fn=os.setsid,
            cwd=CHAIN_SIMULATOR_FOLDER,
            bufsize=1,  # Line-buffered
            universal_newlines=True,  # Decode bytes to strings
        )

        self.stdout_thread = threading.Thread(
            target=self.read_output, args=(self.process.stdout,)
        )
        self.stderr_thread = threading.Thread(
            target=self.read_output, args=(self.process.stderr, True)
        )
        self.stdout_thread.start()
        self.stderr_thread.start()

    def read_output(self, stream, is_error=False):
        """Reads from a stream and stores the output."""
        try:
            for line in stream:
                decoded_line = line.strip()
                if decoded_line:
                    # For debugging purposes, print the captured logs
                    self.logs.put(decoded_line)
                    self.all_logs.append(decoded_line)  # Store the log
                    # print(f"Captured log: {decoded_line}")
        finally:
            stream.close()

    def stop(self):
        if self.process is not None:
            # Send SIGTERM to the process group to cleanly stop all processes
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

            self.process.wait()

            # Ensure output threads are also terminated
            if hasattr(self, "stdout_thread"):
                self.stdout_thread.join()
            if hasattr(self, "stderr_thread"):
                self.stderr_thread.join()

            logger.info("ChainSimulator process and all child processes stopped\n")
        else:
            logger.warning("\nNo ChainSimulator process found.\n")

    def get_first_matching_transaction_selection_log(self, tx_hash, timeout=10):
        """
        Retrieves transaction selection JSON details based on the transaction hash.
        Waits up to 'timeout' seconds for the transaction log to appear.
        """
        start_time = time.time()
        last_index = 0
        pattern = re.compile(
            r'^selection#\d+:\s*(\{"hash":"[0-9a-fA-F]{64}",'
            r'"ppu":\d+,"nonce":\d+,"sender":"[0-9a-fA-F]{64}",'
            r'"gasPrice":\d+,"gasLimit":\d+,"receiver":"[0-9a-fA-F]+","dataLength":\d+\})$'
        )

        while time.time() - start_time < timeout:
            current_logs = self.all_logs[last_index:]
            for log_entry in current_logs:
                if tx_hash in log_entry:
                    json_part_match = pattern.search(log_entry)
                    if json_part_match:
                        json_part = json_part_match.group(1)
                        try:
                            tx_data = json.loads(json_part)
                            if tx_data.get("hash") == tx_hash:
                                return tx_data
                        except json.JSONDecodeError:
                            continue
            last_index = len(self.all_logs)
            time.sleep(0.5)

        raise TimeoutError(
            f"Transaction with hash {tx_hash} not found in logs within {timeout} seconds."
        )
