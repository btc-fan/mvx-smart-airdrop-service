from multiversx_sdk.abi import AddressValue, BigUIntValue
from multiversx_sdk import Address

def bech32_to_hex(bech32_address: str) -> str:
    """
    Converts a Bech32 address to its hexadecimal representation using the MultiversX SDK.
    """
    try:
        address = Address.from_bech32(bech32_address)
        return address.hex()
    except Exception as e:
        print(f"Error converting Bech32 to Hex: {str(e)}")
        return None


def int_to_hex(value: int) -> str:
    """
    Converts an integer to its hexadecimal representation (as a string).
    """
    try:
        return hex(value)[2:]  # Remove the '0x' prefix
    except Exception as e:
        print(f"Error converting int to hex: {str(e)}")
        return None

def string_to_hex(string: str) -> str:
    """
    Converts a string to its hexadecimal representation (as a string).
    """
    try:
        return string.encode("utf-8").hex()
    except Exception as e:
        print(f"Error converting string to hex: {str(e)}")
        return None