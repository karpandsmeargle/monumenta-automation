#!/usr/bin/env python3

import os
import sys
import getopt
import yaml
from pprint import pprint

from lib_py3.item_replacement_manager import ItemReplacementManager
from lib_py3.loot_table_manager import LootTableManager
from lib_py3.iterators.recursive_entity_iterator import get_debug_string_from_entity_path
from lib_py3.common import eprint

from minecraft.chunk_format.schematic import Schematic
from minecraft.world import World

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../quarry"))
from quarry.types import nbt

def usage():
    sys.exit("Usage: {} <--world /path/to/world | --schematics /path/to/schematics> [--logfile <stdout|stderr|path>] [--dry-run]".format(sys.argv[0]))


try:
    opts, args = getopt.getopt(sys.argv[1:], "w:s:l:d", ["world=", "schematics=", "logfile=", "dry-run"])
except getopt.GetoptError as err:
    eprint(str(err))
    usage()

world_path = None
schematics_path = None
logfile = None
dry_run = False

for o, a in opts:
    if o in ("-w", "--world"):
        world_path = a
    elif o in ("-s", "--schematics"):
        schematics_path = a
    elif o in ("-l", "--logfile"):
        logfile = a
    elif o in ("-d", "--dry-run"):
        dry_run = True
    else:
        eprint("Unknown argument: {}".format(o))
        usage()

if world_path is None and schematics_path is None:
    eprint("--world or --schematics must be specified!")
    usage()

loot_table_manager = LootTableManager()
loot_table_manager.load_loot_tables_subdirectories("/home/epic/project_epic/server_config/data/datapacks")
item_replace_manager = ItemReplacementManager(loot_table_manager.get_unique_item_map(show_errors=True))

log_handle = None
if logfile == "stdout":
    log_handle = sys.stdout
elif logfile == "stderr":
    log_handle = sys.stderr
elif logfile is not None:
    log_handle = open(logfile, 'w')

num_replacements = 0
replacements_log = {}

if world_path:
    world = World(world_path)
    for chunk in world.iter_chunks(autosave=(not dry_run)):
        for item in chunk.recursive_iter_items():
            if item_replace_manager.replace_item(item.nbt, log_dict=replacements_log, debug_path=get_debug_string_from_entity_path(item.get_legacy_debug())):
                num_replacements += 1

if schematics_path:
    for root, subdirs, files in os.walk(schematics_path):
        for fname in files:
            if fname.endswith(".schematic"):
                schem = Schematic(os.path.join(root, fname))
                num_replacements_this_schem = 0
                for item in schem.recursive_iter_items():
                    if item_replace_manager.replace_item(item.nbt, log_dict=replacements_log, debug_path=(fname + " -> " + get_debug_string_from_entity_path(item.get_legacy_debug()))):
                        num_replacements += 1
                        num_replacements_this_schem += 1

                if not dry_run and num_replacements_this_schem > 0:
                    schem.save()

if log_handle is not None:
    yaml.dump(replacements_log, log_handle, width=2147483647, allow_unicode=True)

if log_handle is not None and log_handle is not sys.stdout and log_handle is not sys.stderr:
    log_handle.close()

print("Replaced {} items".format(num_replacements))