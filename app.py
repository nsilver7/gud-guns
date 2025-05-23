from flask import Flask, redirect, request, session, url_for, jsonify, render_template
from collections import defaultdict
import requests
import os
import logging
from weapons import extract_weapons

# Load configuration from the config file which reads .env
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

logging.basicConfig(level=logging.INFO)

# Bungie OAuth URLs
BUNGIE_AUTH_URL = 'https://www.bungie.net/en/OAuth/Authorize'
BUNGIE_TOKEN_URL = 'https://www.bungie.net/platform/app/oauth/token/'


@app.route('/')
def home():
    if 'token_data' in session:
        return '''
            <h1>GudGuns App</h1>
            <ul>
                <li><a href="/memberships">View Memberships</a></li>
                <li><a href="/inventory">View Inventory</a></li>
            </ul>
        '''
    return '<a href="/login">Login with Bungie</a>'


@app.route('/login')
def login():
    auth_url = (
        f"{BUNGIE_AUTH_URL}"
        f"?client_id={app.config['CLIENT_ID']}"
        f"&response_type=code"
        f"&redirect_uri={app.config['REDIRECT_URI']}"
    )
    return redirect(auth_url)


@app.route('/oauth_callback')
def oauth_callback():
    app.logger.info("OAuth callback query parameters: %s", request.args)
    code = request.args.get('code')

    if not code:
        app.logger.error("No authorization code received. Query params: %s", request.args)
        return "Error: No authorization code received.", 400

    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': app.config['CLIENT_ID'],
        'client_secret': app.config['CLIENT_SECRET'],
        'redirect_uri': app.config['REDIRECT_URI']
    }
    token_response = requests.post(BUNGIE_TOKEN_URL, data=payload)
    try:
        token_data = token_response.json()
    except Exception as e:
        app.logger.error("Error decoding token JSON: %s", e)
        return "Token JSON decoding error", 500

    app.logger.info("Token data received: %s", token_data)

    # Check if 'access_token' is present and non-empty.
    if not token_data.get("access_token"):
        app.logger.error("No access token found in token_data: %s", token_data)
        return "Authorization failed: access token missing", 500

    session['token_data'] = token_data
    return redirect(url_for('home'))


@app.route('/memberships')
def memberships():
    token_data = session.get('token_data')
    if not token_data:
        return redirect(url_for('home'))

    headers = {
        'X-API-Key': app.config['API_KEY'],
        'Authorization': f'Bearer {token_data.get("access_token")}',
        'Accept': 'application/json'
    }

    logging.info("Headers being sent to Bungie: %s", headers)

    membership_url = 'https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/'
    response = requests.get(membership_url, headers=headers)

    # Log the status code and response text
    print("Memberships endpoint status code:", response.status_code)
    print("Memberships endpoint response text:", response.text)
    
    try:
        data = response.json()
    except Exception as e:
        # Return an error JSON if decoding fails
        return jsonify({
            "error": "Failed to decode JSON from Bungie response",
            "message": str(e),
            "status_code": response.status_code,
            "response_text": response.text
        }), 500

    return jsonify(data)


@app.route('/inventory')
def inventory():
    token_data = session.get('token_data')
    if not token_data:
        return redirect(url_for('home'))
    
    membershipType = '3'
    membershipId = '4611686018540653658'
    
    headers = {
        'X-API-Key': app.config['API_KEY'],
        'Authorization': f'Bearer {token_data.get("access_token")}',
        'Accept': 'application/json'
    }
    
    inventory_url = (
        f'https://www.bungie.net/Platform/Destiny2/{membershipType}/Profile/'
        f'{membershipId}/?components=102,304,306'
    )
    response = requests.get(inventory_url, headers=headers)
    app.logger.info("Inventory endpoint status code: %s", response.status_code)
    app.logger.info("Inventory endpoint raw response: %s", response.text)
    
    try:
        raw_inventory = response.json()
    except Exception as e:
        app.logger.error("Error decoding inventory JSON: %s", e)
        return jsonify({
            "error": "Failed to decode JSON from Bungie response",
            "message": str(e),
            "status_code": response.status_code,
            "response_text": response.text
        }), 500
    
    vault_items = raw_inventory.get("Response", {}) \
                                .get("profileInventory", {}) \
                                .get("data", {}) \
                                .get("items", [])
    app.logger.info("Found %d vault items.", len(vault_items))

    # Extract instance-specific data:
    stats_data = raw_inventory.get("Response", {}).get("itemStats", {}).get("data", {})
    talent_grids_data = raw_inventory.get("Response", {}).get("itemTalentGrids", {}).get("data", {})

    weapon_items = extract_weapons(vault_items, stats_data, talent_grids_data)
    app.logger.info("Total weapon items found: %d", len(weapon_items))
    
    return jsonify(weapon_items)


@app.route('/inventory_ui')
def inventory_ui():
    token_data = session.get('token_data')
    if not token_data:
        return redirect(url_for('home'))
    
    membershipType = '3'
    membershipId = '4611686018540653658'

    headers = {
        'X-API-Key': app.config['API_KEY'],
        'Authorization': f'Bearer {token_data.get("access_token")}',
        'Accept': 'application/json'
    }
    
    # 102 = ProfileInventories, 304 = ItemStats, 306 = ItemTalentGrids, 302 = ItemPerks (if desired)
    inventory_url = (
        f'https://www.bungie.net/Platform/Destiny2/{membershipType}/Profile/'
        f'{membershipId}/?components=102,304,306,302'
    )
    response = requests.get(inventory_url, headers=headers)
    try:
        raw_inventory = response.json()
    except Exception as e:
        return jsonify({
            "error": "Failed to decode JSON from Bungie response",
            "message": str(e)
        }), 500

    app.logger.info("Response keys: %s", list(raw_inventory.get("Response", {}).keys()))
    
    # Extract vault items using the correct path
    vault_items = raw_inventory.get("Response", {}) \
                               .get("profileInventory", {}) \
                               .get("data", {}) \
                               .get("items", [])
    app.logger.info("Found %d vault items.", len(vault_items))
    
    # Extract instance-specific data from itemComponents
    stats_data = raw_inventory.get("Response", {}) \
                              .get("itemComponents", {}) \
                              .get("stats", {}) \
                              .get("data", {})
    talent_grids_data = raw_inventory.get("Response", {}) \
                                     .get("itemComponents", {}) \
                                     .get("talentGrids", {}) \
                                     .get("data", {})
    perks_data = raw_inventory.get("Response", {}) \
                              .get("itemComponents", {}) \
                              .get("perks", {}) \
                              .get("data", {})

    from weapons import extract_weapons
    # Call extract_weapons with vault items and the dynamic component data.
    weapon_items = extract_weapons(vault_items, stats_data, talent_grids_data, perks_data)
    app.logger.info("Total weapon items found: %d", len(weapon_items))
    
    # Group and sort the weapons by type.
    from collections import defaultdict
    grouped_weapons = defaultdict(list)
    for weapon in weapon_items:
        wtype = weapon.get("itemTypeDisplayName", "Other")
        grouped_weapons[wtype].append(weapon)
    
    for wtype in grouped_weapons:
        grouped_weapons[wtype] = sorted(grouped_weapons[wtype], key=lambda w: w.get("name", ""))
    
    return render_template("inventory.html", grouped_weapons=dict(grouped_weapons))


@app.route('/logout')
def logout():
    session.clear()  # Clears all session data
    return redirect(url_for('home'))


@app.route('/debug_token')
def debug_token():
    token = session.get("token_data")
    if token:
        return jsonify(token)
    return "No token found", 404


if __name__ == '__main__':
    # Run the Flask app in debug mode for development.
    app.run(debug=True)
