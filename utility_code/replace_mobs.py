#!/usr/bin/env python3

# For interactive shell
import readline
import code

import sys
import os
import getopt

from lib_py3.mob_replacement_manager import MobReplacementManager, remove_unwanted_spawner_tags
from lib_py3.iterators.recursive_entity_iterator import get_debug_string_from_entity_path
from lib_py3.common import eprint, get_entity_name_from_nbt, get_named_hand_items
from lib_py3.world import World
from lib_py3.library_of_souls import LibraryOfSouls
from lib_py3.schematic import Schematic

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../quarry"))
from quarry.types import nbt

def is_entity_in_spawner(entity_path: [nbt.TagCompound]) -> bool:
    contains_spawner = False
    last = False
    for element in entity_path:
        if element.has_path("SpawnPotentials"):
            contains_spawner = True
            last = True
        else:
            last = False

    return contains_spawner and not last

def match_id(target_id: str, chain=lambda mob: True):
    return lambda mob : mob.at_path("id").value == target_id and chain(mob)

def match_hand(hand: [str], chain=lambda mob: True):
    return lambda mob : mob.has_path('HandItems') and get_named_hand_items(mob) == hand and chain(mob)

def match_name(name: str, chain=lambda mob: True):
    return lambda mob : mob.has_path('CustomName') and get_entity_name_from_nbt(mob) == name and chain(mob)

def match_passenger(host_chain, passenger_chain):
    return lambda mob : (host_chain(mob)
            and mob.has_path('Passengers')
            and len(mob.at_path('Passengers').value) >= 1
            and passenger_chain(mob.at_path('Passengers').value[0]))

# Note that these will be evaluated last to first - so put more broad checks first for performance
sub = [
    ("Lighthouse Defender", match_hand(["Enraged Captain's Axe", "Hawk's Talon"], match_id('minecraft:skeleton'))),
    ("Frost Moon Brute", match_name('6Frost Moon Brute', match_id('minecraft:wither_skeleton'))),
    ("Frost Moon Archer", match_name('Frost Moon Brute', match_id('minecraft:skeleton'))),
    ("Desiccated Ghast", match_name('Dessicated Ghast', match_id('minecraft:ghast'))),


    ("Gear Gremlin", match_passenger(match_id('minecraft:endermite'), match_name('Gear Gremlin', match_id('minecraft:drowned')))),
    ("Rusted Gear", match_passenger(match_id('minecraft:guardian'), match_name('Rusted Gear', match_id('minecraft:drowned')))),
    ("Silver Theurge", match_passenger(match_id('minecraft:silverfish'), match_name('Silver Theurge', match_id('minecraft:drowned')))),

    ("Pirate Buccaneer", match_name('Pirate Buckaneer', match_id('minecraft:husk'))),
    ("Pirate Oarsman", match_name('Pirate Oarman', match_id('minecraft:vindicator'))),

    # Pink same-named mobs
    ("Fall Citizen", match_hand(["Earthbound Runeblade", None], match_name("Tempered Citizen", match_id('minecraft:zombie_villager')))),
    ("Summer Citizen", match_hand(["Lingering Flame", None], match_name("Tempered Citizen", match_id('minecraft:zombie_villager')))),
    ("Spring Citizen", match_hand(["Rosethorn Blade", "Talaya's Blossom"], match_name("Tempered Citizen", match_id('minecraft:zombie_villager')))),
    ("Winter Citizen", match_hand(["Iceborn Runeblade", None], match_name("Tempered Citizen", match_id('minecraft:zombie_villager')))),
    ("Fall Watcher", match_hand(["Soulvenom Bow", None], match_name("Tempered Watcher", match_id('minecraft:skeleton')))),
    ("Summer Watcher", match_hand(["Ishkarian Longbow", None], match_name("Tempered Watcher", match_id('minecraft:skeleton')))),
    ("Spring Watcher", match_hand(["Steelsiege", None], match_name("Tempered Watcher", match_id('minecraft:skeleton')))),
    ("Winter Watcher", match_hand(["Icicle Greatbow", None], match_name("Tempered Watcher", match_id('minecraft:skeleton')))),
]

def usage():
    sys.exit("Usage: {} <--world /path/to/world | --schematics /path/to/schematics> <--library-of-souls /path/to/library-of-souls.json> [--logfile <stdout|stderr|path>] [--dry-run]".format(sys.argv[0]))

try:
    opts, args = getopt.getopt(sys.argv[1:], "w:s:b:l:di", ["world=", "schematics=", "library-of-souls=", "logfile=", "dry-run"])
except getopt.GetoptError as err:
    eprint(str(err))
    usage()

world_path = None
schematics_path = None
library_of_souls_path = None
logfile = None
dry_run = False

for o, a in opts:
    if o in ("-w", "--world"):
        world_path = a
    elif o in ("-s", "--schematics"):
        schematics_path = a
    elif o in ("-b", "--library-of-souls"):
        library_of_souls_path = a
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
elif library_of_souls_path is None:
    eprint("--library-of-souls must be specified!")
    usage()

los = LibraryOfSouls(library_of_souls_path, readonly=True)
replace_mgr = MobReplacementManager()
los.load_replacements(replace_mgr)
replace_mgr.add_substitutions(sub)

log_handle = None
if logfile == "stdout":
    log_handle = sys.stdout
elif logfile == "stderr":
    log_handle = sys.stderr
elif logfile is not None:
    log_handle = open(logfile, 'w')

replacements_log = {}

mobs_replaced = 0
try:
    # This is handy here because it has direct access to previously defined globals
    def process_entity(entity: nbt.TagCompound, source_pos, entity_path: [nbt.TagCompound], debug_path="") -> None:
        global mobs_replaced

        if entity.has_path("Delay"):
            entity.at_path("Delay").value = 0

            # Remove pigs
            if entity.has_path('SpawnPotentials'):
                new_potentials = []
                for nested_entity in entity.at_path('SpawnPotentials').value:
                    if nested_entity.has_path('Entity.id') and nested_entity.at_path('Entity.id').value == "minecraft:pig":
                        if log_handle is not None:
                            log_handle.write("Removing pig from SpawnPotentials at {}\n".format(get_debug_string_from_entity_path(entity_path)))
                    else:
                        new_potentials.append(nested_entity)
                entity.at_path('SpawnPotentials').value = new_potentials
            if entity.has_path("SpawnData.id") and entity.at_path("SpawnData.id").value == "minecraft:pig":
                if log_handle is not None:
                    log_handle.write("Removing pig Spawndata at {}\n".format(get_debug_string_from_entity_path(entity_path)))
                entity.value.pop("SpawnData")


        if is_entity_in_spawner(entity_path):
            remove_unwanted_spawner_tags(entity)
            if replace_mgr.replace_mob(entity, replacements_log, debug_path + get_debug_string_from_entity_path(entity_path)):
                mobs_replaced += 1

    if world_path:
        world = World(world_path)
        debug_path = os.path.basename(world_path) + " -> "
        for entity, source_pos, entity_path in world.entity_iterator(readonly=dry_run):
            process_entity(entity, source_pos, entity_path, debug_path=debug_path)

    if schematics_path:
        for root, subdirs, files in os.walk(schematics_path):
            for fname in files:
                if fname.endswith(".schematic"):
                    debug_path = fname + " -> "
                    schem = Schematic(os.path.join(root, fname))
                    for entity, source_pos, entity_path in schem.entity_iterator(readonly=dry_run):
                        process_entity(entity, source_pos, entity_path, debug_path=debug_path)

                    if not dry_run:
                        schem.save()

    print("{} mobs replaced".format(mobs_replaced))

finally:
    if log_handle is not None:
        for to_mob in replacements_log:
            log_handle.write("{}\n".format(to_mob))
            log_handle.write("    TO:\n")
            log_handle.write("        {}\n".format(replacements_log[to_mob]["TO"]))
            log_handle.write("    FROM:\n")

            for from_mob in replacements_log[to_mob]["FROM"]:
                log_handle.write("        {}\n".format(from_mob))

                for from_location in sorted(replacements_log[to_mob]["FROM"][from_mob]):
                    log_handle.write("            {}\n".format(from_location))

            log_handle.write("\n")

    if log_handle is not None and log_handle is not sys.stdout and log_handle is not sys.stderr:
        log_handle.close()