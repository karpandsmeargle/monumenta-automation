#!/usr/bin/env python3

import os
import sys
import json
from lib_py3.common import get_entity_name_from_nbt
from pprint import pprint

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../quarry"))

from quarry.types.nbt import TagCompound

if __name__ == '__main__':
    with open(sys.argv[1], "r") as fp:
        souls = json.load(fp)

    location_set = set()

    for soul in souls:
        if "location_names" in soul:
            for loc in soul["location_names"]:
                location_set.add(loc)

    print("Removed mobs:")
    new_souls = []
    for soul in souls:
        if "location_names" in soul and len(soul["location_names"]) > 0:
            # Only keep the most recent history elemnt
            soul["history"] = [soul["history"][0],]
            new_souls.append(soul)
        else:
            name = get_entity_name_from_nbt(TagCompound.from_mojangson(soul["history"][0]["mojangson"]), True)
            print("  " + name)

    print("\n\n\nAll locations:")
    for name in sorted(location_set):
        print("  " + name)

    with open(sys.argv[1], "w") as fp:
        souls = json.dump(new_souls, fp, ensure_ascii=False, sort_keys=False, indent=2, separators=(',', ': '))

