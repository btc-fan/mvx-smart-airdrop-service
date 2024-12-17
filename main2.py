from multiversx_sdk import Address


def bech32_to_hex(bech32_address: str) -> str:
    """
    Converts a Bech32 address to its hexadecimal representation using the MultiversX SDK.
    """
    try:
        # Use MultiversX SDK for conversion
        address = Address.from_bech32(bech32_address)
        return address.hex()
    except Exception as e:
        print(f"Error converting Bech32 to Hex: {str(e)}")
        return None


async def prompt_conversion_and_show_result(bech32_address: str) -> dict:
    """
    Converts Bech32 to Hex using a Python function and integrates the result into an AI prompt.
    """
    # Step 1: Convert Bech32 address to Hex
    hex_address = bech32_to_hex(bech32_address)

    if not hex_address:
        return {"error": "Failed to convert Bech32 to Hex"}

    # Step 2: Construct the AI prompt to validate and display the conversion
    prompt = f"""
    Convert the following Bech32 address to its Hexadecimal format:
    Bech32: {bech32_address}
    Hexadecimal: {hex_address}
    
    Ensure the provided Hexadecimal address is accurate. Respond with a JSON object in the format:
    {{
        "bech32": "{bech32_address}",
        "hex": "{hex_address}"
    }}
    """

    try:
        # Execute the prompt using the AI agent
        response = await execute_prompt(prompt)
        print(f"AI Response for Conversion: {response.strip()}")
        return response.strip()
    except Exception as e:
        print(f"Error during AI prompt execution: {str(e)}")
        return {"error": "AI processing failed"}


async def main():
    # Example Bech32 address
    bech32_address = "erd1t9cs66523zq290w0u4s5evjmpvn2m0wapjsa486dn9zvmh60kxnqcj8zx4"

    # Convert and integrate with AI prompt
    response = await prompt_conversion_and_show_result(bech32_address)

    print("Final Conversion and Validation Response:", response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
