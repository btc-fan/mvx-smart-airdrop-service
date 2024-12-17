import json

from multiversx_sdk import Address
from quart import Quart, request, jsonify
from quart_cors import cors
from llm_agents.agents import fetch_address_details, fetch_esdt_details, validate_bech32_addresses, \
    create_multi_esdt_transfer_transaction

from python_files.config import provider

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
        sender = data.get("sender", "")
        receivers = data.get("receivers", [])
        token_identifier = "TKN-1a2b3c"
        amount = int(data.get("amount", 0))
        contract_address = data.get("contractAddress", "")
        chain_id = data.get("chainId", "")
        host = "https://devnet-gateway.multiversx.com"
        print(f"Host: {host}, Sender: {sender}, Receivers: {receivers}, Token: {token_identifier}, Amount: {amount}")

        # Validate addresses (sender and receivers)
        # print("Validating Bech32 addresses...")
        # all_addresses = receivers + [sender]
        # are_all_valid = await validate_bech32_addresses(all_addresses)
        #
        #
        # if not bool(are_all_valid):
        #     print("Address validation failed. Some addresses are invalid.")
        #     return jsonify({"error": "One or more addresses are invalid"}), 400


        # # Fetch Address Details
        # print(f"Fetching address details for {sender}...")
        # address_details = await fetch_address_details(host, sender)
        # print("Fetched Address Details:", address_details)
        sender_address = Address.new_from_bech32(sender)
        sender_on_network = provider.get_account(sender_address)

        address_details = {'data': {'account': {'address': 'erd138cn6lupfdgn3euh29acrrnp5l8g5vy9ax249zp0j8wd03k3y42qttsz8g', 'nonce': 1025, 'balance': '597563760000000000', 'username': '', 'code': '', 'codeHash': None, 'rootHash': '3Zt4TxfQ9P3viFo5yJejXfdsZ6RZeoftLsKb4GSyYZ8=', 'codeMetadata': None, 'developerReward': '0', 'ownerAddress': ''}, 'blockInfo': {'nonce': 967104, 'hash': 'af05df13cd04ef3c3f5cf0b65c748434fb3e6f3876ee21e93437fb6679555937', 'rootHash': '33f564b8c45f90a49f49a95b0f23217abd3d10c3230dad138f62a356a0f42bd2'}}, 'error': '', 'code': 'successful'}

        # Validate balance in address details
        # account_data = address_details.get("data", {}).get("account", {})
        # address_balance = int(account_data.get("balance", "0"))
        address_balance = sender_on_network.balance
        print(f"Sender's EGLD Balance: {address_balance}")

        if address_balance <= 0:
            print("Insufficient EGLD balance.")
            return jsonify({"error": "Sender's EGLD balance is insufficient (must be greater than 0)"}), 400

        # Fetch ESDT Details
        print(f"Fetching ESDT details for {sender}...")
        esdt_details = await fetch_esdt_details(host, sender)
        print("Fetched ESDT Details:", esdt_details)

        # Parse the ESDT data
        # esdt_details = {'data': {'blockInfo': {'hash': '16074bffd3900da8428e41c759b3f89f707b4db5ceda36c7962f432cf1416991', 'nonce': 967105, 'rootHash': '33f564b8c45f90a49f49a95b0f23217abd3d10c3230dad138f62a356a0f42bd2'}, 'esdts': {'SNOW-13d1ef': {'balance': '99999999969000', 'tokenIdentifier': 'SNOW-13d1ef', 'type': 'FungibleESDT'}, 'TKN-1a2b3c': {'balance': '100000000000000', 'tokenIdentifier': 'SNOW-896a35', 'type': 'FungibleESDT'}, 'SNOW-ed984b': {'balance': '100000000000000', 'tokenIdentifier': 'SNOW-ed984b', 'type': 'FungibleESDT'}, 'WINTER-994654': {'balance': '9000000000000000', 'tokenIdentifier': 'WINTER-994654', 'type': 'FungibleESDT'}}}, 'error': '', 'code': 'successful'}

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


        # Create MultiESDTNFTTransfer Transaction
        print("Creating MultiESDTNFTTransfer transaction...")
        esdt_amount = 7777
        service_address = "erd15uchpdmkn90qxd9add6npnst3mckkapkq7zmn5l8rlkwnvk7k0ese9q8z5"
        # contract_address = "erd1tvz9hk4lzsn57rltj7r06n9vjxtpr30f3n52tujuvznl37zhd8vq5uzxxx"
        amounts = [555,999]
        transaction = await create_multi_esdt_transfer_transaction(chain_id=chain_id,esdt_amount=esdt_amount, service_address=service_address, amounts=amounts, sender=sender, receivers=receivers, token_identifier=token_identifier, contract_address=contract_address, nonce=sender_on_network.nonce)

        if "error" in transaction:
            print("Failed to create transaction:", transaction["error"])
            return jsonify({"error": transaction["error"]}), 500

        # Prepare response
        response_data = {
            "status": "success",
            "transaction": transaction,
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
