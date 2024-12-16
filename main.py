import asyncio

import pandas as pd
import ollama
from quart import Quart, request, jsonify
from quart_cors import cors

from llm_agents.agents import execute_prompt, fetch_address_details, fetch_esdt_details

app = Quart("SmartAirdrop")
app = cors(app)

@app.route('/fetch-details', methods=['OPTIONS', 'POST'])
async def fetch_details():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

    try:
        # Get the address from the POST request
        data = await request.get_json()
        host = data.get("host", "https://testnet-gateway.multiversx.com")
        address = data.get("address", "erd138cn6lupfdgn3euh29acrrnp5l8g5vy9ax249zp0j8wd03k3y42qttsz8g")

        if not address:
            return jsonify({"error": "No address provided"}), 400

        # Fetch details concurrently
        address_details_task = fetch_address_details(host, address)
        esdt_details_task = fetch_esdt_details(host, address)

        address_details, esdt_details = await asyncio.gather(address_details_task, esdt_details_task)

        return jsonify({
            "address_details": address_details,
            "esdt_details": esdt_details
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _build_cors_preflight_response():
    """Helper function to build the preflight response."""
    response = jsonify({"message": "CORS preflight successful"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
