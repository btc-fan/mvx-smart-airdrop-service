import asyncio
import json
import subprocess


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
    Build a valid URL to fetch ESDT details for "{address}" from the host "{host}".
    Example: {host}/address/{address}/esdt. Pls return only the URL without any additional text
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