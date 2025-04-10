import json

# Load the manifest file into memory.
with open("DestinyInventoryItemDefinition.json", "r") as f:
    item_definitions = json.load(f)

# Define a set of weapon category hash values (adjust these as needed).
weapon_category_hashes = {
    5,              # Auto Rifle
    6,              # Hand Cannon
    7,              # Pulse Rifle
    8,              # Scout Rifle
    14,             # Sidearm
    3954685534,     # Submachine Guns
    3317538576,     # Combat Bows (Bows)
    9,              # Fusion Rifle
    3871742104,     # Glaives
    11,             # Shotgun
    10,             # Sniper Rifle
    2489664120,     # Trace Rifle
    13,             # Rocket Launcher
    1504945536,     # Linear Fusion Rifle
    54,             # Sword
    153950757,      # Grenade Launcher
    12              # Machine Gun
}

def is_weapon(definition):
    """Return True if the given definition has any of the known weapon category hashes."""
    cats = definition.get("itemCategoryHashes", [])
    return any(cat in weapon_category_hashes for cat in cats)


def enrich_item(vault_item):
    """Enrich a vault item with static data from the manifest using itemHash."""
    item_hash = vault_item.get("itemHash")
    definition = item_definitions.get(str(item_hash))
    if not definition:
        return vault_item

    display = definition.get("displayProperties", {})
    enriched = {}
    enriched.update(vault_item)
    enriched["name"] = display.get("name", "Unknown")
    enriched["description"] = display.get("description", "")
    enriched["icon"] = display.get("icon", "")
    enriched["itemTypeDisplayName"] = definition.get("itemTypeDisplayName", "Unknown")
    enriched["tierTypeName"] = definition.get("tierTypeName", "Unknown")
    enriched["itemCategoryHashes"] = definition.get("itemCategoryHashes", [])
    return enriched


def enrich_item_instance(vault_item, stats_data, talent_grids_data, perks_data):
    """Merge instance-specific details using the itemInstanceId."""
    enriched = enrich_item(vault_item)
    instance_id = vault_item.get("itemInstanceId")
    if instance_id:
        enriched["instanceStats"] = stats_data.get(instance_id, {})
        enriched["instanceTalentGrid"] = talent_grids_data.get(instance_id, {})
        enriched["instancePerks"] = perks_data.get(instance_id, {})
    else:
        enriched["instanceStats"] = {}
        enriched["instanceTalentGrid"] = {}
        enriched["instancePerks"] = {}
    return enriched


def extract_weapons(vault_items, stats_data, talent_grids_data, perks_data):
    weapons = []
    for vault_item in vault_items:
        item_hash = vault_item.get("itemHash")
        definition = item_definitions.get(str(item_hash))
        if definition and is_weapon(definition):
            enriched = enrich_item_instance(vault_item, stats_data, talent_grids_data, perks_data)
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