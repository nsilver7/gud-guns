import json

# Load the manifest file into memory.
with open("DestinyInventoryItemDefinition.json", "r") as f:
    item_definitions = json.load(f)

# Define a set of weapon category hash values (adjust these as needed).
weapon_category_hashes = {
    5,        # Auto Rifle
    6,        # Hand Cannon
    7,        # Pulse Rifle
    8,        # Scout Rifle
    14,       # Sidearm
    3954685534,  # Submachine Guns
    3317538576,  # Combat Bows (Bows)
    9,        # Fusion Rifle
    3871742104,  # Glaives
    11,       # Shotgun
    10,       # Sniper Rifle
    2489664120,  # Trace Rifle
    13,       # Rocket Launcher
    1504945536,  # Linear Fusion Rifle
    54,       # Sword
    153950757,   # Grenade Launcher
    12        # Machine Gun
}

def is_weapon(definition):
    """Return True if the given definition has any of the known weapon category hashes."""
    cats = definition.get("itemCategoryHashes", [])
    return any(cat in weapon_category_hashes for cat in cats)


def enrich_item(vault_item):
    """
    Given a vault item (with minimal data from the API),
    look up its definition via itemHash and merge the two.
    """
    item_hash = vault_item.get("itemHash")
    definition = item_definitions.get(str(item_hash))
    # If there is no definition, return the original vault item.
    if not definition:
        return vault_item

    # Prepare an enriched dictionary.
    enriched = {}
    # Copy instance-level data from the vault item.
    enriched.update(vault_item)
    # Merge in static data from the definition.
    display = definition.get("displayProperties", {})
    enriched["name"] = display.get("name", "Unknown")
    enriched["description"] = display.get("description", "")
    enriched["icon"] = display.get("icon", "")
    enriched["itemTypeDisplayName"] = definition.get("itemTypeDisplayName", "Unknown")
    enriched["tierTypeName"] = definition.get("tierTypeName", "Unknown")
    enriched["itemCategoryHashes"] = definition.get("itemCategoryHashes", [])
    # You could also add other relevant keys from the definition if needed.
    return enriched


def extract_weapons(vault_items):
    """
    Filters the list of vault items (each with an itemHash) for weapons,
    enriching each item using its manifest definition.
    """
    weapons = []
    for vault_item in vault_items:
        enriched = enrich_item(vault_item)
        # Check if the enriched definition qualifies as a weapon.
        definition = item_definitions.get(str(vault_item.get("itemHash")))
        if definition and is_weapon(definition):
            weapons.append(enriched)
    return weapons



"""
Loading the Manifest:
The file DestinyInventoryItemDefinition.json is loaded into the dictionary item_definitions, where keys are item hashes (as strings).

is_weapon Function:
This function checks the list of category hashes in the definition to see if any match those in our weapon_category_hashes set. This filtering is more robust than a regex search on display names.

enrich_item Function:
It takes the minimal vault item (with keys like itemHash, quantity, etc.), looks up its full definition in the manifest, and merges key display properties (name, icon, description, etc.) into a single enriched dictionary.

extract_weapons Function:
It loops over each vault item, enriches it, and then checks (via the definition) if it qualifies as a weapon. Only those that are weapons are returned.
"""