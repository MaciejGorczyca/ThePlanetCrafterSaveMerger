import json
import sys
from collections import Counter

def read_save(file_path):
    # utf-8-sig automatically handles the hidden BOM (Byte Order Mark) at the start of the file
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    sections = [sec.strip() for sec in content.split('@')]
    parsed_sections = []
    for sec in sections:
        if not sec:
            parsed_sections.append([])
            continue
        items = [json.loads(item.strip()) for item in sec.split('|') if item.strip()]
        parsed_sections.append(items)
    return parsed_sections

def write_save(parsed_sections, output_path):
    stringified_sections = []
    for sec in parsed_sections:
        if not sec:
            stringified_sections.append("")
        else:
            stringified_sections.append("|".join([json.dumps(item, separators=(',', ':')) for item in sec]))
    
    final_output = "@\n".join(stringified_sections)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_output)

def merge_saves(old_save_path, new_save_path, output_path):
    print("Loading saves...")
    old_data = read_save(old_save_path)
    new_data = read_save(new_save_path)

    # --- AUTO-DETECT TARGET PLANET HASH ---
    planet_hashes = [wo.get("planet") for wo in new_data[3] if wo.get("planet") not in (None, 0)]
    if not planet_hashes:
        print("ERROR: Could not detect a target planet in the new save!")
        return
    
    target_planet_hash = Counter(planet_hashes).most_common(1)[0][0]
    
    # Grab the planet string name for UI/logging
    target_planet_name = "Unknown"
    for p in new_data[1]:
        target_planet_name = p.get("planetId", "Unknown")
        
    print(f"Auto-detected Target Planet: {target_planet_name} (Hash: {target_planet_hash})")

    # --- SECTION 0: World State ---
    print("Merging World State...")
    old_world_state = old_data[0][0]
    new_world_state = new_data[0][0]
    
    old_world_state["terraTokens"] += new_world_state.get("terraTokens", 0)
    old_world_state["allTimeTerraTokens"] += new_world_state.get("allTimeTerraTokens", 0)
    
    old_unlocks = set(old_world_state.get("unlockedGroups", "").split(","))
    new_unlocks = set(new_world_state.get("unlockedGroups", "").split(","))
    merged_unlocks = old_unlocks.union(new_unlocks)
    old_world_state["unlockedGroups"] = ",".join(filter(None, merged_unlocks))

    # --- SECTION 1: Planets ---
    print("Merging Planet Data...")
    for p in new_data[1]:
        if p.get("planetId") == target_planet_name:
            old_data[1].append(p)

    # --- SECTION 6 & 7: Messages and Events ---
    print("Merging Messages and Events...")
    old_msgs = {m["stringId"] for m in old_data[6]}
    for m in new_data[6]:
        if m["stringId"] not in old_msgs:
            old_data[6].append(m)
            
    old_events = {e["stringId"] for e in old_data[7]}
    for e in new_data[7]:
        if e["stringId"] not in old_events:
            old_data[7].append(e)

    # --- SECTIONS 3 & 4: Extraction ---
    print(f"Extracting {target_planet_name} WorldObjects and Inventories...")
    new_wos = {wo["id"]: wo for wo in new_data[3]}
    new_invs = {inv["id"]: inv for inv in new_data[4]}
    
    tox_wos = {}
    tox_invs = {}

    # Pass 1: Find base objects explicitly on the target planet
    for wo in new_wos.values():
        if wo.get("planet") == target_planet_hash:
            tox_wos[wo["id"]] = wo

    # Pass 2: Recursively trace all linked inventories and items
    sizes_changed = True
    while sizes_changed:
        start_wo_len = len(tox_wos)
        start_inv_len = len(tox_invs)

        # Find inventories attached to our current extracted WOs
        for wo in list(tox_wos.values()):
            if wo.get("liId") and wo["liId"] in new_invs:
                tox_invs[wo["liId"]] = new_invs[wo["liId"]]
            if wo.get("siIds"):
                for sid in wo["siIds"].split(","):
                    if sid and int(sid) in new_invs: 
                        tox_invs[int(sid)] = new_invs[int(sid)]
        
        # Find items (WOs) inside our current extracted Inventories
        for inv in list(tox_invs.values()):
            if inv.get("woIds"):
                for wid in inv["woIds"].split(","):
                    if wid and int(wid) in new_wos:
                        tox_wos[int(wid)] = new_wos[int(wid)]

        if len(tox_wos) == start_wo_len and len(tox_invs) == start_inv_len:
            sizes_changed = False

    print(f"Extracted {len(tox_wos)} WorldObjects and {len(tox_invs)} Inventories.")

    # --- ID REMAPPING ENGINE ---
    print("Remapping IDs...")
    old_wo_ids = {wo["id"] for wo in old_data[3]}
    old_inv_ids = {inv["id"] for inv in old_data[4]}
    
    # Dynamic Safe Starts
    current_new_wo_id = max(210000000, max(old_wo_ids) + 1 if old_wo_ids else 210000000)
    current_new_inv_id = max(old_inv_ids) + 10000 if old_inv_ids else 10000
    
    wo_id_map = {}
    inv_id_map = {}

    for wo_id, wo in tox_wos.items():
        if wo_id < 200000000:
            # Scene Object: Should be unique by map design
            if wo_id in old_wo_ids:
                print(f"WARNING: Map Scene Object collision at ID {wo_id}. Remapping, but this might detach it from map generation.")
                wo_id_map[wo_id] = current_new_wo_id
                current_new_wo_id += 1
            else:
                wo_id_map[wo_id] = wo_id # Keep original
        else:
            # Player built object: Remap safely
            wo_id_map[wo_id] = current_new_wo_id
            current_new_wo_id += 1

    for inv_id in tox_invs.keys():
        inv_id_map[inv_id] = current_new_inv_id
        current_new_inv_id += 1

    # Apply mappings to WOs
    for wo in tox_wos.values():
        wo["id"] = wo_id_map[wo["id"]]
        if wo.get("liId") and wo["liId"] in inv_id_map:
            wo["liId"] = inv_id_map[wo["liId"]]
        if wo.get("siIds"):
            new_sids = [str(inv_id_map[int(sid)]) for sid in wo["siIds"].split(",") if sid and int(sid) in inv_id_map]
            wo["siIds"] = ",".join(new_sids)
        if wo.get("linkedWo") and wo["linkedWo"] in wo_id_map:
            wo["linkedWo"] = wo_id_map[wo["linkedWo"]]
        old_data[3].append(wo)

    # Apply mappings to Inventories
    for inv in tox_invs.values():
        inv["id"] = inv_id_map[inv["id"]]
        if inv.get("woIds"):
            new_wids = [str(wo_id_map[int(wid)]) for wid in inv["woIds"].split(",") if wid and int(wid) in wo_id_map]
            inv["woIds"] = ",".join(new_wids)
        old_data[4].append(inv)

    # --- SECTION 9: Procedural Generation ---
    if len(new_data) > 9 and len(old_data) > 9:
        print("Merging Procedural Generation Data...")
        for proc in new_data[9]:
            if proc.get("planet") == target_planet_hash:
                # Remap generated/dropped strings
                if proc.get("woIdsGenerated"):
                    new_gen = [str(wo_id_map[int(wid)]) for wid in proc["woIdsGenerated"].split(",") if wid and int(wid) in wo_id_map]
                    proc["woIdsGenerated"] = ",".join(new_gen)
                if proc.get("woIdsDropped"):
                    new_drop = [str(wo_id_map[int(wid)]) for wid in proc["woIdsDropped"].split(",") if wid and int(wid) in wo_id_map]
                    proc["woIdsDropped"] = ",".join(new_drop)
                old_data[9].append(proc)

    print("Writing merged save file...")
    write_save(old_data, output_path)
    print(f"Success! Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python merge_saves.py <Base_Save.json> <DLC_Save.json> <Merged_Output.json>")
    else:
        merge_saves(sys.argv[1], sys.argv[2], sys.argv[3])