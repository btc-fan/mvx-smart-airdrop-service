import json


from quart import Quart, request, jsonify
from quart_cors import cors

from llm_agents.agents import fetch_address_details, fetch_esdt_details

app = Quart("SmartAirdrop")
app = cors(app)


@app.route('/airdrop', methods=['OPTIONS', 'POST'])
async def airdrop():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    try:
        # Get input parameters from the POST request
        data = await request.get_json()
        host = data.get("host", "https://testnet-gateway.multiversx.com")
        sender = data.get("sender", "")
        token_identifier = data.get("tokenIdentifier", "")
        amount = int(data.get("amount", 0))

        if not host or not sender or not token_identifier or amount <= 0:
            return jsonify({"error": "Invalid input parameters"}), 400

        # Fetch Address Details
        address_details_raw = await fetch_address_details(host, sender)
        try:
            address_details = json.loads(address_details_raw)
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse address details response"}), 500

        # Validate balance in address details
        account_data = address_details.get("data", {}).get("account", {})
        address_balance = int(account_data.get("balance", "0"))

        if address_balance <= 0:
            return jsonify({"error": "Sender's EGLD balance is insufficient (must be greater than 0)"}), 400

        # Fetch ESDT Details
        esdt_details_raw = await fetch_esdt_details(host, sender)
        try:
            esdt_details = json.loads(esdt_details_raw)
        except json.JSONDecodeError:
            return jsonify({"error": "Failed to parse ESDT details response"}), 500

        # Parse the ESDT data
        esdt_data = esdt_details.get("data", {}).get("esdts", {})
        sender_token = esdt_data.get(token_identifier)

        if not sender_token:
            return jsonify({"error": f"Token {token_identifier} not found for sender {sender}"}), 400

        sender_balance = int(sender_token.get("balance", "0"))

        if sender_balance < amount:
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

        return jsonify(response_data)

    except Exception as e:
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
