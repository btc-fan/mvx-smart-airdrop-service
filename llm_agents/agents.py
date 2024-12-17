import asyncio
import json
import subprocess

from main2 import bech32_to_hex
from utils.data_converstion import string_to_hex, int_to_hex


async def execute_prompt(prompt: str) -> str:
    """
    Sends a prompt to Llama 3.2 and returns the response.
    """
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["ollama", "run", "gemma2:27b"],
            input=prompt,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()  # Return the output from the model
    except subprocess.CalledProcessError as e:
        return json.dumps({"error": f"AI agent error: {e.stderr.strip()}"})  # Return error as JSON



async def validate_bech32_addresses(addresses: list) -> bool:
    """
    Validates an array of Bech32 addresses using Ollama.
    Returns True if all addresses are valid, otherwise False.
    """
    prompt = f"""
        Bech32 addresses must meet the following strict rules:
        1. Start with a human-readable part (HRP) of lowercase letters (a-z) and optionally digits (0-9). It must not start with a digit or invalid characters like '1', 'b', 'i', or 'o'.
        2. Include exactly one separator ('1') between the HRP and data part.
        3. The data part contains only these valid characters: 'q', 'p', 'z', 'r', 'y', '9', 'x', '8', 'g', 'f', '2', 't', 'v', 'd', 'w', '0', 's', '3', 'j', 'n', '5', '4', 'k', 'h', 'c', 'e', '6', 'm', 'u', 'a', '7'. Uppercase letters and invalid characters like 'b', 'i', 'o', or '1' (except as the separator) are not allowed.
        4. Have a total length of 42 to 62 characters.
        5. No leading/trailing spaces or invalid prefixes like '1' or non-alphanumeric symbols.
        6. HRP must follow expected conventions (e.g., 'erd' for MultiversX). Invalid prefixes like '1erd' or 'xxx' are not allowed.
        
        Addresses to validate:
        {addresses}
        
        Validate each address against the rules:
        - Respond "True" if all addresses are valid.
        - Respond "False" if any address is invalid.
        
        Your response must be a **single word**, either "True" or "False". No explanations or extra text.

        """
    response = await execute_prompt(prompt)
    print(f"Validation response for addresses {addresses}: {response}")
    return response.strip().lower() == "true"





async def fetch_address_details(host: str, address: str) -> dict:
    """
    Fetches the address details by building the URL with AI and executing the curl command.
    """
    prompt = f"""
    Build a valid URL to fetch address details for "{address}" from the host "{host}".
    Example: {host}/address/{address}. Pls return only the URL without any additional text
    """
    try:
        # Get the URL from the AI prompt
        url = await execute_prompt(prompt)
        print(f"Constructed URL for address details: {url}")

        # Execute the curl command
        result = await asyncio.to_thread(
            subprocess.run,
            ["curl", url.strip()],
            text=True,
            capture_output=True,
            check=True
        )
        return json.loads(result.stdout.strip())  # Parse the JSON response
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to fetch address details: {e.stderr.strip()}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse address details response."}


async def fetch_esdt_details(host: str, address: str) -> dict:
    """
    Fetches the ESDT token details by building the URL with AI and executing the curl command.
    """
    prompt = f"""
    Construct a valid URL to fetch ESDT token details. 
    The URL must adhere to the following rules:
    1. It should use the provided host and address parameters.
    2. The format must be: {host}/address/{address}/esdt.
    3. Only output the URL. Do not include any additional text or explanations.
    
    Input:
    - Host: {host}
    - Address: {address}
    
    Output:
    A single valid URL.
    """
    try:
        # Get the URL from the AI prompt
        url = await execute_prompt(prompt)
        print(f"Constructed URL for ESDT details: {url}")

        # Execute the curl command
        result = await asyncio.to_thread(
            subprocess.run,
            ["curl", url.strip()],
            text=True,
            capture_output=True,
            check=True
        )
        return json.loads(result.stdout.strip())  # Parse the JSON response
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to fetch ESDT details: {e.stderr.strip()}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse ESDT details response."}


async def create_multi_esdt_transfer_transaction(
        chain_id, sender, receivers, token_identifier, esdt_amount, contract_address, nonce, service_address, amounts
):
    """
    Creates a MultiESDTNFTTransfer transaction JSON using an AI agent.
    Dynamically generates the data field for all receivers and amounts.
    """
    try:
        # Convert Bech32 fields to Hex
        contract_hex = bech32_to_hex(contract_address)
        service_hex = bech32_to_hex(service_address)
        sender_hex = bech32_to_hex(sender)
        receiver_hexes = [bech32_to_hex(receiver) for receiver in receivers]
        gas_limit = max(1_500_000 * len(receivers), 10_000_000)
        gas_price = 1000000000

        if not contract_hex or not service_hex or not sender_hex or None in receiver_hexes:
            return {"error": "Failed to convert Bech32 to Hex for one or more addresses"}

        # Calculate wrapped EGLD dynamically
        wrapped_egld = int(0.01 * len(receivers) * (10 ** 18))
        wrapped_egld_hex = int_to_hex(wrapped_egld)

        # Convert token identifier and amounts to Hex
        token_identifier_hex = string_to_hex(token_identifier)
        esdt_amount_hex = int_to_hex(int(esdt_amount))
        amounts_hex = [int_to_hex(int(amount)) for amount in amounts]

        if None in [token_identifier_hex, wrapped_egld_hex, esdt_amount_hex] or None in amounts_hex:
            return {"error": "Failed to convert values to Hex"}

        # Generate the data dynamically using AI agents
        prompt = f"""
        You are tasked with generating a MultiESDTNFTTransfer transaction.
        - Use the contract address: {contract_hex}
        - Use the service address: {service_hex}
        - Token Identifier: {token_identifier_hex}
        - Wrapped EGLD: {wrapped_egld_hex}
        - ESDT Amount: {esdt_amount_hex}
        - Sender: {sender_hex}
        - Receivers: {receiver_hexes}
        - Amounts: {['{:02x}'.format(int(amount, 16)).zfill(2) for amount in amounts_hex]}

        Construct the 'data' field in the following format:
        MultiESDTNFTTransfer@<contract_address>@02@5745474c442d613238633539@@<wrapped_egld>@<token_identifier>@@<esdt_amount>@736d61727453617665@<service_address>@<receiver_1>@<amount_1>@<receiver_2>@<amount_2>...

        Rules:
        - Always maintain `@@` between values where indicated.
        - Pad all hex numbers to ensure they have an odd number of characters by adding a leading `0` if necessary. 
          For example, `13e` becomes `013e`.
        - Pad all amounts (e.g., <amount_1>, <amount_2>) to an even number of hex characters to maintain two-character representation for values like `1` (e.g., `01`).

        Only return the constructed 'data' field, no explanations or additional text.
        """
        # Execute the AI prompt
        response = await execute_prompt(prompt)
        data_field = response.strip()

        # Construct the transaction object
        transaction = {
            "nonce": nonce,
            "value": "0",
            "receiver": sender,  # Contract interaction typically uses sender as receiver
            "sender": sender,
            "senderUsername": "",
            "receiverUsername": "",
            "gasPrice": gas_price,
            "gasLimit": gas_limit,
            "data": data_field,
            "chainID": chain_id,
            "version": 2,
            "options": 0,
            "guardian": "",
            "signature": "",
            "guardianSignature": "",
            "relayer": "",
            "relayerSignature": ""
        }

        # Log the generated transaction
        print("Generated Transaction:", transaction)
        return transaction

    except Exception as e:
        print(f"Error creating transaction: {str(e)}")
        return {"error": f"Failed to create transaction: {str(e)}"}


async def user_prompt_to_json(user_prompt: str) -> any:
    """
    Converts the user prompt into a JSON format with correctly extracted values.
    """
    """
    Converts the user prompt into a JSON format with correctly extracted values.
    """
    prompt = f"""
    Convert the following prompt into a valid JSON format. Extract the `tokenIdentifier`, `amount`, and `receivers`. 
    Use the following example for guidance:

    Example input:
    "Send 1 BUILDO-22c0a5 to the following addresses erd1a9wdz7pdyttectxjntg4z83unkal7pj5ycfem5ynzh49j8st4mas52yhel, erd139adwtgs4smel4rmqlphcxp8q8jr5qsxrfwlluhzvds3elk3hm2qq3vnnc"

    Example output:
    {{
      "tokenIdentifier": "VALUE",
      "amount": VALUE,
      "receivers": [
        "VALUE",
        "VALUE"
      ]
    }}
    
    Only return the JSON, without any additional explanation. For the user's prompt: "{user_prompt}", generate the corresponding JSON output without json markers.
    """
    response = await execute_prompt(prompt)
    print("response: " + response)
    return response
