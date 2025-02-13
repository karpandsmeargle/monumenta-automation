#!/usr/bin/env pypy3

import sys
import getopt
import json
import math
import multiprocessing
import traceback

from lib_py3.common import eprint
from minecraft.world import World

def usage():
    sys.exit("Usage: {} <--world /path/to/world> <--output file.json | --input file.json> [--pos1 x,y,z --pos2 x,y,z] [--num-threads num]".format(sys.argv[0]))

def out_region_iter(region):
    out = []
    for chunk in region.iter_chunks(autosave=False):
        for block_entity in chunk.recursive_iter_block_entities():
            if block_entity.nbt.has_path('Command'):
                block = chunk.get_block(block_entity.pos)

                # Check that we're actually exactly within the bounding box (inclusive)
                bpos = block_entity.pos
                if bpos[0] < min_x or bpos[1] < min_y or bpos[2] < min_z or bpos[0] > max_x or bpos[1] > max_y or bpos[2] > max_z:
                    continue

                block_name = block['name']

                entry = {}
                entry['pos'] = block_entity.pos
                entry['command'] = block_entity.nbt.at_path('Command').value
                entry['name'] = block_name
                entry['auto'] = block_entity.nbt.at_path('auto').value
                entry['powered'] = block_entity.nbt.at_path('powered').value
                if 'facing' in block:
                    entry['facing'] = block['facing']
                else:
                    entry['facing'] = None

                out.append(entry)

    return out

def err_func(ex, args):
    eprint(f"Caught exception: {ex}")
    eprint(f"While iterating: {args}")
    eprint(traceback.format_exc())
    return []

if __name__ == '__main__':
    multiprocessing.set_start_method("fork")

    try:
        opts, args = getopt.getopt(sys.argv[1:], "j:", ["world=", "output=", "input=", "pos1=", "pos2=", "num-threads="])
    except getopt.GetoptError as err:
        eprint(str(err))
        usage()

    world_path = None
    output_path = None
    input_path = None
    pos1 = (-math.inf, -math.inf, -math.inf)
    pos2 = (math.inf, math.inf, math.inf)
    num_threads = 4

    for o, a in opts:
        if o in ("--world",):
            world_path = a
        elif o in ("--output",):
            output_path = a
        elif o in ("--input",):
            input_path = a
        elif o in ("--pos1",):
            try:
                split = a.split(",")
                pos1 = (int(split[0]), int(split[1]), int(split[2]))
            except Exception:
                eprint("Invalid --pos1 argument")
                usage()
        elif o in ("--pos2",):
            try:
                split = a.split(",")
                pos2 = (int(split[0]), int(split[1]), int(split[2]))
            except Exception:
                eprint("Invalid --pos2 argument")
                usage()
        elif o in ("-j", "--num-threads"):
            num_threads = int(a)
        else:
            eprint("Unknown argument: {}".format(o))
            usage()

    if world_path is None:
        eprint("--world must be specified!")
        usage()
    elif (input_path is None) and (output_path is None):
        eprint("Either --input or --output must be specified!")
        usage()
    elif (input_path is not None) and (output_path is not None):
        eprint("Only one of --input or --output can be specified!")
        usage()
    elif ((pos1 is not None) and (pos2 is None)) or ((pos1 is None) and (pos2 is not None)):
        eprint("--pos1 and --pos2 must be specified (or neither specified)!")
        usage()


    world = World(world_path)

    output_mode = (input_path is None)

    min_x = min(pos1[0], pos2[0])
    min_y = min(pos1[1], pos2[1])
    min_z = min(pos1[2], pos2[2])
    max_x = max(pos1[0], pos2[0])
    max_y = max(pos1[1], pos2[1])
    max_z = max(pos1[2], pos2[2])

    if output_mode:
        results = world.iter_regions_parallel(out_region_iter, err_func, num_processes=num_threads, min_x=min_x, min_y=min_y, min_z=min_z, max_x=max_x, max_y=max_y, max_z=max_z)
        out = []
        for result in results:
            for item in result:
                out.append(item)

        with open(output_path, 'w') as outfile:
            json.dump(out, outfile, ensure_ascii=False, sort_keys=False, indent=2, separators=(',', ': '))

        print(f"Wrote {len(out)} command blocks to {output_path}")

    else:
        # Build a map of all the commands that need updating
        # key = "x y z"
        # value = { pos/command/name/auto/powered }
        commands = {}
        num_to_replace = 0
        with open(input_path, 'r') as outfile:
            data = json.load(outfile)
            for element in data:
                if "command_block" not in element["name"]:
                    eprint("Warning: Refusing to update command block contained within an item: ", json.dumps(element))
                else:
                    commands[f"{element['pos'][0]} {element['pos'][1]} {element['pos'][2]}"] = element
                    num_to_replace += 1

        # Iterate the world and update things from the map
        # Not much reason to do this in parallel, but could be done with a little work
        num_replaced = 0
        for region in world.iter_regions(min_x=min_x, min_y=min_y, min_z=min_z, max_x=max_x, max_y=max_y, max_z=max_z):
            for chunk in region.iter_chunks(min_x=min_x, min_y=min_y, min_z=min_z, max_x=max_x, max_y=max_y, max_z=max_z, autosave=False):
                changed = False
                for block_entity in chunk.recursive_iter_block_entities():
                    if block_entity.nbt.has_path('Command'):
                        command_to_load = commands.get(f"{block_entity.pos[0]} {block_entity.pos[1]} {block_entity.pos[2]}", None)
                        if command_to_load is not None:
                            # Only update the command itself, none of the other stats
                            block_entity.nbt.at_path('Command').value = command_to_load["command"]
                            num_replaced += 1
                            changed = True
                if changed:
                    region.save_chunk(chunk)

        print(f"{num_replaced} / {num_to_replace} command blocks updated")
