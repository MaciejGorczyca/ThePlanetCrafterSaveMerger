# The Planet Crafter - Save File Merger

A Python utility designed to merge progress from different planets (e.g., DLC planets like *Humble* or *Toxicity*) into a single, master save file. 

This tool allows you to play a new DLC on a fresh save file, and later merge that planet, your base, your inventory, and your global unlocks back into your main, long-term save file.

## Features
* **Dynamic ID Remapping:** The game uses hardcoded integer IDs for every item, chest, and building. Simple copy-pasting corrupts the save. This script assigns new, safe IDs (starting above 210,000,000) to imported objects to guarantee zero collisions with your existing base.
* **Recursive Inventory Tracing:** Automatically finds all containers on the target planet and traces their nested inventories to ensure no items are left behind.
* **Auto-Detection:** Automatically detects the DLC planet hash in the new save file. Future-proofed for upcoming DLCs.
* **Global Progress Merging:** Combines Terra Tokens, unlocked blueprints, story events, and read messages.

## Prerequisites
* Python 3.6 or higher.
* No external libraries required (uses standard `json` and `collections`).

## Usage

**⚠️ CRITICAL: ALWAYS BACKUP YOUR SAVE FILES BEFORE PROCEEDING! ⚠️**

Save files are typically located at:
`C:\Users\<YourUser>\AppData\LocalLow\MijuGames\Planet Crafter`

1. Open your terminal or command prompt.
2. Run the script using the following syntax:
   ```bash
   python merge_saves.py <Base_Save.json> <DLC_Save.json> <Merged_Output.json>
   ```
   * `<Base_Save.json>`: Your main, long-term save file.
   * `<DLC_Save.json>`: The save file containing the new planet you want to import.
   * `<Merged_Output.json>`: The name of the new file the script will create.

**Example:**
```bash
python merge_saves.py MainSave.json ToxicityRun.json MergedSave.json
```

3. Move the resulting `MergedSave.json` into your Planet Crafter save directory.
4. Launch the game and load `MergedSave`. 

## Known Quirks & Notes
* **Map Scene Object Collisions:** You may see a console warning like `WARNING: Map Scene Object collision at ID...`. This is normal. It means a pre-placed rock or ruin shared an ID across saves. The script safely remaps it to prevent corruption.
* **Spawning Under the Map:** The first time you use a rocket/teleporter to travel to the newly merged planet, you might spawn under the terrain. This is a Unity physics loading quirk. Simply jetpack out of the ground, or save and reload your game while on the planet to fix your position.
* **Player Position:** Your player character will spawn exactly where they were in the `<Base_Save.json>`.

## Included Tools
* `merge_saves.py`: The main merging engine.
* `extract_schema.py`: A developer tool used to parse the custom `@` and `|` delimited save format and output a lightweight JSON schema for debugging.
