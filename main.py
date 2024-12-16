import json
from quart import Quart, request, jsonify
from quart_cors import cors
from llm_agents.agents import fetch_address_details, fetch_esdt_details, validate_bech32_addresses

app = Quart("SmartAirdrop")
app = cors(app)


@app.route('/airdrop', methods=['OPTIONS', 'POST'])
async def airdrop():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    try:
        # Get input parameters from the POST request
        data = await request.get_json()
        print("Received input data:", data)

        host = data.get("host", "https://testnet-gateway.multiversx.com")
        sender = data.get("sender", "")
        receivers = data.get("receivers", [])
        token_identifier = data.get("tokenIdentifier", "")
        amount = int(data.get("amount", 0))

        print(f"Host: {host}, Sender: {sender}, Receivers: {receivers}, Token: {token_identifier}, Amount: {amount}")

        if not host or not sender or not receivers or not token_identifier or amount <= 0:
            print("Invalid input parameters.")
            return jsonify({"error": "Invalid input parameters"}), 400

        # Validate addresses (sender and receivers)
        print("Validating Bech32 addresses...")
        all_addresses = receivers + [sender]
        are_all_valid = await validate_bech32_addresses(all_addresses)


        if not bool(are_all_valid):
            print("Address validation failed. Some addresses are invalid.")
            return jsonify({"error": "One or more addresses are invalid"}), 400


        # Fetch Address Details
        print(f"Fetching address details for {sender}...")
        address_details = await fetch_address_details(host, sender)
        print("Fetched Address Details:", address_details)

        # Validate balance in address details
        account_data = address_details.get("data", {}).get("account", {})
        address_balance = int(account_data.get("balance", "0"))
        print(f"Sender's EGLD Balance: {address_balance}")

        if address_balance <= 0:
            print("Insufficient EGLD balance.")
            return jsonify({"error": "Sender's EGLD balance is insufficient (must be greater than 0)"}), 400

        # Fetch ESDT Details
        print(f"Fetching ESDT details for {sender}...")
        esdt_details = await fetch_esdt_details(host, sender)
        print("Fetched ESDT Details:", esdt_details)

        # Parse the ESDT data
        esdt_data = esdt_details.get("data", {}).get("esdts", {})
        print("Parsed ESDT Data:", esdt_data)
        sender_token = esdt_data.get(token_identifier)

        if not sender_token:
            print(f"Token {token_identifier} not found for sender {sender}.")
            return jsonify({"error": f"Token {token_identifier} not found for sender {sender}"}), 400

        sender_balance = int(sender_token.get("balance", "0"))
        print(f"Sender's Token Balance: {sender_balance}")

        if sender_balance < amount:
            print("Insufficient token balance for the airdrop.")
            return jsonify({"error": "Insufficient token balance for the airdrop"}), 400

        # Prepare response for the next agent or step
        response_data = {
            "status": "success",
            "message": f"Sufficient funds available for the airdrop of {amount} {token_identifier}.",
            "sender_address": sender,
            "token_balance": sender_balance,
            "egld_balance": address_balance,
            "required_amount": amount,
            "token_identifier": token_identifier
        }
        print("Final Response Data:", response_data)

        return jsonify(response_data)

    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


def _build_cors_preflight_response():
    """Helper function to build the preflight response."""
    response = jsonify({"message": "CORS preflight successful"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
