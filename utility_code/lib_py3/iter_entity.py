#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../quarry"))
from quarry.types import nbt

itemTagPaths = (
    "ArmorItems[]",
    "ArmorItem",
    "EnderItems[]",
    "HandItems[]",
    "Inventory[]",
    "Item",
    "Items[]",
    "Inventory[]",
    "Offers.Recipes[].buy",
    "Offers.Recipes[].buyB",
    "Offers.Recipes[].sell",
    "RecordItem",
    "SaddleItem",
    "Trident",
)

entityTagPaths = (
    "Passengers[]",
)

