import asyncio
import subprocess

import ollama
from typing import List

import pandas as pd


async def execute_prompt(prompt):
    """
    Sends a prompt to Llama 3.2 and returns the response.
    """
    try:
        # Execute the ollama command asynchronously using asyncio.to_thread
        result = await asyncio.to_thread(
            subprocess.run,
            ["ollama", "run", "llama3.2-vision"],
            input=prompt,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()  # Return the output from the model
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

BASE_URL = "https://gateway.multiversx.com/address"

async def fetch_address_details(host: str, address: str) -> dict:
    """
    Fetches the address details from the specified host and address.
    """
    try:
        url = f"{host}/address/{address}"
        result = await asyncio.to_thread(
            subprocess.run,
            ["curl", url],
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to fetch address details: {e.stderr.strip()}"}


async def fetch_esdt_details(host: str, address: str) -> dict:
    """
    Fetches the ESDT tokens from the specified host and address.
    """
    try:
        url = f"{host}/address/{address}/esdt"
        result = await asyncio.to_thread(
            subprocess.run,
            ["curl", url],
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to fetch ESDT details: {e.stderr.strip()}"}
