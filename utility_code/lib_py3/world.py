#!/usr/bin/env python3

import os
import sys
import uuid

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../quarry"))
from quarry.types import nbt
from quarry.types.chunk import BlockArray
from quarry.types.buffer import BufferUnderrun

from lib_py3.block_map import block_map

class World(object):
    """
    An object for editing a world (1.13+).
    Gives methods for editing blocks and areas that
    may cross over chunks or region files.

    The path you provide is expected to contain a level.dat file.
    """
    def __init__(self,path):
        """
        Load a world folder, fetching the list of region files and players that it contains.
        """
        self.path = path
        self.level_dat_file = nbt.NBTFile.load( os.path.join( path,'level.dat' ) )
        self.level_dat = self.level_dat_file.root_tag.body
        self.find_region_files()
        self.find_players()
        self.find_data_packs()

    def save(self):
        self.level_dat_file.save( os.path.join( self.path, 'level.dat' ) )

    def find_region_files(self):
        self.region_files = []

        for filename in os.listdir( os.path.join( self.path, 'region' ) ):
            filename_parts = filename.split('.')
            if (
                len(filename_parts) != 4 or
                filename_parts[0] != 'r' or
                filename_parts[3] != 'mca'
            ):
                continue
            try:
                coords = (
                    int( filename_parts[1] ),
                    int( filename_parts[2] )
                )
                self.region_files.append( coords )
            except:
                pass

    def find_players(self):
        self.players = []

        for filename in os.listdir( os.path.join( self.path, 'playerdata' ) ):
            try:
                player = uuid.UUID( filename[:-4] )
                self.players.append( player )
            except:
                pass

    def find_data_packs(self):
        self.enabled_data_packs = []
        self.disabled_data_packs = []

        if self.level_dat.has_path('Data.DataPacks.Disabled'):
            for datapack in self.level_dat.at_path('Data.DataPacks.Disabled').value:
                self.disabled_data_packs.append(datapack.value)

        if self.level_dat.has_path('Data.DataPacks.Enabled'):
            for datapack in self.level_dat.at_path('Data.DataPacks.Enabled').value:
                self.enabled_data_packs.append(datapack.value)

    def save_data_packs(self):
        if not self.level_dat.has_path('Data.DataPacks'):
            self.level_dat.at_path('Data').value['DataPacks'] = nbt.TagCompound({})

        if not self.level_dat.has_path('Data.DataPacks.Disabled'):
            self.level_dat.at_path('Data.DataPacks').value['Disabled'] = nbt.TagList({})

        if not self.level_dat.has_path('Data.DataPacks.Enabled'):
            self.level_dat.at_path('Data.DataPacks').value['Enabled'] = nbt.TagList({})

        enabled = []
        disabled = []

        for datapack in self.enabled_data_packs:
            enabled.append( nbt.TagString( datapack ) )

        for datapack in self.disabled_data_packs:
            if datapack not in self.enabled_data_packs:
                disabled.append( nbt.TagString( datapack ) )

        self.level_dat.at_path('Data.DataPacks.Disabled').value = disabled
        self.level_dat.at_path('Data.DataPacks.Enabled').value = enabled

        self.find_data_packs()

    @property
    def spawn(self):
        x = self.level_dat.at_path('Data.SpawnX').value
        y = self.level_dat.at_path('Data.SpawnY').value
        z = self.level_dat.at_path('Data.SpawnZ').value

        return (x,y,z)

    @spawn.setter
    def spawn(self,pos):
        if len(pos) != 3:
            raise IndexError('pos must have 3 entries, xyz')
        paths = ['SpawnX','SpawnY','SpawnZ']
        for i in range(3):
            self.level_dat.at_path( 'Level.' + paths[i] ).value = pos[i]

    def dump_command_blocks(self,pos1,pos2,log=None):
        """
        Finds all command blocks between pos1 and pos2,
        and displays what they contain. (WIP)
        """
        min_x = min(pos1[0],pos2[0])
        min_y = min(pos1[1],pos2[1])
        min_z = min(pos1[2],pos2[2])

        max_x = max(pos1[0],pos2[0])
        max_y = max(pos1[1],pos2[1])
        max_z = max(pos1[2],pos2[2])

        required_cy_sections = tuple(self._bounded_range(min_y,max_y,0,256,16))

        command_blocks = []
        
        if log:
            log_file = open(log,'w')

        for rz in range(min_z//512,max_z//512+1):
            for rx in range(min_x//512,max_x//512+1):
                region_path = os.path.join( self.path, "region", "r.{}.{}.mca".format(rx, rz) )

                if not os.path.isfile(region_path):
                    continue

                with nbt.RegionFile(region_path) as region:
                    for cz in self._bounded_range(min_z,max_z,rz,512,16):
                        for cx in self._bounded_range(min_x,max_x,rx,512,16):
                            try:
                                chunk = region.load_chunk(cx, cz)

                                if not chunk.body.has_path('Level.TileEntities'):
                                    continue

                                # Load the blocks in the chunk sections now in case we find command block entities
                                chunk_sections = {}
                                for section in chunk.body.at_path('Level.Sections').value:
                                    cy = section.at_path("Y").value
                                    if cy not in required_cy_sections:
                                        continue
                                    chunk_sections[cy] = BlockArray.from_nbt(section, block_map)

                                #blocks[256 * by + 16 * bz + bx] = block['block']

                                for tile_entity in chunk.body.at_path('Level.TileEntities').value:
                                    tile_x = tile_entity.at_path('x').value
                                    tile_y = tile_entity.at_path('y').value
                                    tile_z = tile_entity.at_path('z').value
                                    if not (
                                        tile_entity.at_path('id').value == 'minecraft:command_block' and
                                        min_x <= tile_x and tile_x <= max_x and
                                        min_y <= tile_y and tile_y <= max_y and
                                        min_z <= tile_z and tile_z <= max_z
                                    ):
                                        continue

                                    command_blocks.append(tile_entity)

                                    cy = tile_y // 16

                                    bx = tile_x & 0xf
                                    by = tile_y & 0xf
                                    bz = tile_z & 0xf

                                    block = chunk_sections[cy][256 * by + 16 * bz + bx]
                                    block_id = block['name']
                                    #conditional = block['conditional']
                                    #facing = block['facing']

                                    Command = tile_entity.at_path('Command').value
                                    if tile_entity.has_path('LastOutput'):
                                        LastOutput = tile_entity.at_path('LastOutput').value
                                    else:
                                        LastOutput = ''
                                    if tile_entity.has_path('LastExecution'):
                                        LastExecution = tile_entity.at_path('LastExecution').value
                                    else:
                                        LastExecution = 0

                                    reason = None
                                    if LastExecution <= 559266554:
                                        reason = 'last used 1.12'
                                    elif len(Command) == 0:
                                        reason = 'no command'
                                    elif '"arguement' in LastOutput:
                                        reason = 'bad arguements'
                                    elif '"command.context.here"' in LastOutput:
                                        reason = 'output indicates error'

                                    if reason and log:
                                        # This command block hasn't been updated, or has an error
                                        log_file.write( '{0:>7} {1:>7} {2:>7} {3:<36}{4:<25}{5}\n'.format(tile_x,tile_y,tile_z,block_id,reason,Command) )

                            except BufferUnderrun:
                                # Chunk not loaded
                                pass

        if log:
            log_file.close()
        return(command_blocks)

    def get_block(self,pos):
        """
        Get the block at position (x,y,z).
        Example block:
        {
            'block': {
                'facing': 'north',
                'waterlogged': 'false',
                'name': 'minecraft:wall_sign'
            },
            'nbt': '{keepPacked:0b,x:-1441,Text4:"{\\"text\\":\\"\\"}",y:2,Text3:"{\\"text\\":\\"\\"}",z:-1444,Text2:"{\\"text\\":\\"\\"}",id:"minecraft:sign",Text1:"{\\"text\\":\\"\\"}"}'
        }

        Liquids are not yet supported
        """
        x,y,z = pos
        # bx,by,bz are block coordinates within the chunk section
        rx, bx = divmod(x, 512)
        by = y
        rz, bz = divmod(z, 512)
        cx, bx = divmod(bx, 16)
        cy, by = divmod(by, 16)
        cz, bz = divmod(bz, 16)

        region_path = os.path.join( self.path, "region", "r.{}.{}.mca".format(rx, rz) )

        with nbt.RegionFile(region_path) as region:
            chunk = region.load_chunk(cx, cz)
            section_not_found = True
            for section in chunk.body.at_path('Level.Sections').value:
                if section.at_path('Y').value == cy:
                    section_not_found = False
                    blocks = BlockArray.from_nbt(section, block_map)

                    result = {'block':blocks[256 * by + 16 * bz + bx]}
                    if chunk.body.has_path('Level.TileEntities'):
                        for tile_entity in chunk.body.at_path('Level.TileEntities').value:
                            if (
                                tile_entity.at_path('x').value == x and
                                tile_entity.at_path('y').value == y and
                                tile_entity.at_path('z').value == z
                            ):
                                result['nbt'] = tile_entity.to_mojangson()
                                break

                    return result
            if section_not_found:
                raise Exception("Chunk section not found")

    def set_block(self,pos,block):
        """
        Set a block at position (x,y,z).
        Example block:
        {'block': {'snowy': 'false', 'name': 'minecraft:grass_block'} }

        In this version:
        - All block properties are mandatory (no defaults are filled in for you)
        - Block NBT cannot be set, but can be read.
        - Existing block NBT for the specified coordinate is cleared.
        - Liquids are not yet supported
        """
        x,y,z = pos
        # bx,by,bz are block coordinates within the chunk section
        rx, bx = divmod(x, 512)
        by = y
        rz, bz = divmod(z, 512)
        cx, bx = divmod(bx, 16)
        cy, by = divmod(by, 16)
        cz, bz = divmod(bz, 16)

        region_path = os.path.join( self.path, "region", "r.{}.{}.mca".format(rx, rz) )

        with nbt.RegionFile(region_path) as region:
            chunk = region.load_chunk(cx, cz)
            for section in chunk.body.at_path('Level.Sections').value:
                if section.value['Y'].value == cy:
                    blocks = BlockArray.from_nbt(section, block_map)
                    blocks[256 * by + 16 * bz + bx] = block['block']

                    if chunk.body.has_path('Level.TileEntities'):
                        NewTileEntities = []
                        for tile_entity in chunk.body.at_path('Level.TileEntities').value:
                            if (
                                tile_entity.at_path('x').value != x or
                                tile_entity.at_path('y').value != y or
                                tile_entity.at_path('z').value != z
                            ):
                                NewTileEntities.append(tile_entity)
                        if len(NewTileEntities) == 0:
                            chunk.body.at_path('Level').value.pop('TileEntities')
                        else:
                            chunk.body.at_path('Level.TileEntities').value = NewTileEntities

                    region.save_chunk(chunk)
                    break
            else:
                raise Exception("Chunk section not found")

    def _bounded_range(self,min_in,max_in,range_start,range_length,divide=1):
        """
        Clip the input so the start and end don't exceed some other range.
        range_start is multiplied by range_length before use
        The output is relative to the start of the range.
        divide allows the range to be scaled to ( range // divide )
        """
        range_length //= divide
        range_start *= range_length

        min_out = min_in//divide - range_start
        max_out = max_in//divide - range_start + 1

        min_out = max( 0, min( min_out, range_length ) )
        max_out = max( 0, min( max_out, range_length ) )

        return range( min_out, max_out )

    def fill_blocks(self,pos1,pos2,block):
        """
        Fill the blocks from pos1 to pos2 (x,y,z).
        Example block:
        {'block': {'snowy': 'false', 'name': 'minecraft:grass_block'} }

        In this version:
        - All block properties are mandatory (no defaults are filled in for you)
        - Block NBT cannot be set, but can be read.
        - Similar to the vanilla /fill command, entities are ignored.
        - Existing block NBT for the specified coordinate is cleared.
        - Liquids are not yet supported
        """
        min_x = min(pos1[0],pos2[0])
        min_y = min(pos1[1],pos2[1])
        min_z = min(pos1[2],pos2[2])

        max_x = max(pos1[0],pos2[0])
        max_y = max(pos1[1],pos2[1])
        max_z = max(pos1[2],pos2[2])

        required_cy_sections = tuple(self._bounded_range(min_y,max_y,0,256,16))

        for rz in range(min_z//512,max_z//512+1):
            for rx in range(min_x//512,max_x//512+1):
                region_path = os.path.join( self.path, "region", "r.{}.{}.mca".format(rx, rz) )

                if not os.path.isfile(region_path):
                    raise FileNotFoundError('No such region {},{} in world {}'.format(rx,rz,self.path))

                with nbt.RegionFile(region_path) as region:
                    for cz in self._bounded_range(min_z,max_z,rz,512,16):
                        for cx in self._bounded_range(min_x,max_x,rx,512,16):
                            chunk = region.load_chunk(cx, cz)
                            chunk_sections = chunk.body.at_path('Level.Sections').value
                            required_sections_left = set(required_cy_sections)

                            # Handle blocks - eventually liquids, lighting, etc will be handled here too
                            for section in chunk_sections:
                                cy = section.at_path("Y").value
                                if cy not in required_sections_left:
                                    continue
                                required_sections_left.remove(cy)
                                blocks = BlockArray.from_nbt(section, block_map)

                                for by in self._bounded_range(min_y,max_y,cy,16):
                                    for bz in self._bounded_range(min_z,max_z,32*rz+cz,16):
                                        for bx in self._bounded_range(min_x,max_x,32*rx+cx,16):
                                            blocks[256 * by + 16 * bz + bx] = block['block']

                            if len(required_sections_left) != 0:
                                raise KeyError( 'Could not find cy={} in chunk {},{} of region file {},{} in world {}'.format(required_sections_left,cx,cz,rx,rz,self.path) )

                            # Handle tile entities
                            if chunk.body.has_path('Level.TileEntities'):
                                NewTileEntities = []
                                for tile_entity in chunk.body.at_path('Level.TileEntities').value:
                                    tile_x = tile_entity.at_path('x').value
                                    tile_y = tile_entity.at_path('y').value
                                    tile_z = tile_entity.at_path('z').value
                                    if not (
                                        min_x <= tile_x and tile_x <= max_x and
                                        min_y <= tile_y and tile_y <= max_y and
                                        min_z <= tile_z and tile_z <= max_z
                                    ):
                                        NewTileEntities.append(tile_entity)
                                if len(NewTileEntities) == 0:
                                    chunk.body.at_path('Level').value.pop('TileEntities')
                                else:
                                    chunk.body.at_path('Level.TileEntities').value = NewTileEntities

                            region.save_chunk(chunk)

    def replace_blocks(self,pos1,pos2,old_blocks,new_block):
        """
        Replace old_blocks from pos1 to pos2 (x,y,z).

        old_blocks is a list of the blocks to replace.
        If an entry in old_blocks leaves out a block state, it will match any value for that state.

        new_block is what those blocks are replaced with.

        Example block:
        {'block': {'snowy': 'false', 'name': 'minecraft:grass_block'} }

        In this version:
        - All block properties are mandatory (no defaults are filled in for you)
        - Block NBT cannot be set, but can be read.
        - Similar to the vanilla /fill command, entities are ignored.
        - Existing block NBT for the specified coordinate is cleared.
        - Liquids are not yet supported
        """
        min_x = min(pos1[0],pos2[0])
        min_y = min(pos1[1],pos2[1])
        min_z = min(pos1[2],pos2[2])

        max_x = max(pos1[0],pos2[0])
        max_y = max(pos1[1],pos2[1])
        max_z = max(pos1[2],pos2[2])

        required_cy_sections = tuple(self._bounded_range(min_y,max_y,0,256,16))

        for rz in range(min_z//512,max_z//512+1):
            for rx in range(min_x//512,max_x//512+1):
                region_path = os.path.join( self.path, "region", "r.{}.{}.mca".format(rx, rz) )

                if not os.path.isfile(region_path):
                    raise FileNotFoundError('No such region {},{} in world {}'.format(rx,rz,self.path))

                with nbt.RegionFile(region_path) as region:
                    for cz in self._bounded_range(min_z,max_z,rz,512,16):
                        for cx in self._bounded_range(min_x,max_x,rx,512,16):
                            chunk = region.load_chunk(cx, cz)
                            chunk_sections = chunk.body.at_path('Level.Sections').value
                            required_sections_left = set(required_cy_sections)

                            # Handle blocks - eventually liquids, lighting, etc will be handled here too
                            for section in chunk_sections:
                                cy = section.at_path("Y").value
                                if cy not in required_sections_left:
                                    continue
                                required_sections_left.remove(cy)
                                blocks = BlockArray.from_nbt(section, block_map)

                                for by in self._bounded_range(min_y,max_y,cy,16):
                                    for bz in self._bounded_range(min_z,max_z,32*rz+cz,16):
                                        for bx in self._bounded_range(min_x,max_x,32*rx+cx,16):
                                            block = blocks[256 * by + 16 * bz + bx]

                                            for old_block in old_blocks:
                                                match = True

                                                for key in old_block['block']:
                                                    if (
                                                        key not in block or
                                                        old_block['block'][key] != block[key]
                                                    ):
                                                        match = False
                                                        break

                                                if not match:
                                                    break

                                                # Replace the block
                                                blocks[256 * by + 16 * bz + bx] = new_block

                                                x = 512*rx + 16*cx + bx
                                                y =          16*cy + by
                                                z = 512*rz + 16*cz + bz

                                                # Handle tile entities
                                                if chunk.body.has_path('Level.TileEntities'):
                                                    NewTileEntities = []
                                                    for tile_entity in chunk.body.at_path('Level.TileEntities').value:
                                                        tile_x = tile_entity.at_path('x').value
                                                        tile_y = tile_entity.at_path('y').value
                                                        tile_z = tile_entity.at_path('z').value
                                                        if not (
                                                            x == tile_x and
                                                            y == tile_y and
                                                            z == tile_z
                                                        ):
                                                            NewTileEntities.append(tile_entity)
                                                    if len(NewTileEntities) == 0:
                                                        chunk.body.at_path('Level').value.pop('TileEntities')
                                                    else:
                                                        chunk.body.at_path('Level.TileEntities').value = NewTileEntities

                            region.save_chunk(chunk)

    def restore_area(self,pos1,pos2,old_world):
        """
        Restore the area in pos1,po2 in this world
        to how it was in old_world at the same coordinates.

        In this version:
        - Restoring an area that's missing in one world or the other results in an error
        - This MAY include subchunks, testing required. In this case, F3+G to show chunk
          borders, the blue lines mark subchunks. Make sure each subchunk has at least
          one block in it, and this should work fine. Air and air variants don't count.
        """
        min_x = min(pos1[0],pos2[0])
        min_y = min(pos1[1],pos2[1])
        min_z = min(pos1[2],pos2[2])

        max_x = max(pos1[0],pos2[0])
        max_y = max(pos1[1],pos2[1])
        max_z = max(pos1[2],pos2[2])

        required_cy_sections = tuple(self._bounded_range(min_y,max_y,0,256,16))

        for rz in range(min_z//512,max_z//512+1):
            for rx in range(min_x//512,max_x//512+1):
                new_region_path = os.path.join( self.path, "region", "r.{}.{}.mca".format(rx, rz) )
                old_region_path = os.path.join( old_world.path, "region", "r.{}.{}.mca".format(rx, rz) )

                if not os.path.isfile(new_region_path):
                    raise FileNotFoundError('No such region {},{} in world {}'.format(rx,rz,self.path))
                if not os.path.isfile(old_region_path):
                    raise FileNotFoundError('No such region {},{} in world {}'.format(rx,rz,old_world.path))

                with nbt.RegionFile(new_region_path) as new_region:
                    with nbt.RegionFile(old_region_path) as old_region:
                        for cz in self._bounded_range(min_z,max_z,rz,512,16):
                            for cx in self._bounded_range(min_x,max_x,rx,512,16):
                                new_chunk = new_region.load_chunk(cx, cz)
                                old_chunk = old_region.load_chunk(cx, cz)
                                """
                                NOTE: loading the old chunk in this way does NOT
                                affect the old world, as long as we don't save
                                the chunk back.
                                No deep copy is required past here.
                                """

                                new_chunk_sections = {}
                                old_chunk_sections = {}

                                for new_chunk_section in new_chunk.body.at_path('Level.Sections').value:
                                    cy = new_chunk_section.at_path("Y").value
                                    new_chunk_sections[cy] = new_chunk_section

                                for old_chunk_section in old_chunk.body.at_path('Level.Sections').value:
                                    cy = old_chunk_section.at_path("Y").value
                                    old_chunk_sections[cy] = old_chunk_section

                                old_only_sections = set(old_chunk_sections.keys()).difference(set(new_chunk_sections.keys()))
                                new_only_sections = set(new_chunk_sections.keys()).difference(set(old_chunk_sections.keys()))
                                common_sections = set(old_chunk_sections.keys()).intersection(set(new_chunk_sections.keys()))

                                ################################################
                                # Handle blocks
                                for cy in old_only_sections:
                                    # Copy, deleting blocks if out of bounds
                                    old_section = old_chunk_sections[cy]
                                    old_blocks = BlockArray.from_nbt(old_section, block_map)

                                    for by in set(range(16)).difference(set( self._bounded_range(min_y,max_y,cy,16) )):
                                        for bz in set(range(16)).difference(set( self._bounded_range(min_z,max_z,32*rz+cz,16) )):
                                            for bx in set(range(16)).difference(set( self._bounded_range(min_x,max_x,32*rx+cx,16) )):
                                                index = 256 * by + 16 * bz + bx
                                                old_blocks[index] = {'name': 'minecraft:air'}

                                    new_chunk.body.at_path('Level.Sections').value.append(old_section)

                                for cy in new_only_sections:
                                    # Blocks need deleting if in bounds
                                    new_section = new_chunk_sections[cy]
                                    new_blocks = BlockArray.from_nbt(new_section, block_map)

                                    for by in self._bounded_range(min_y,max_y,cy,16):
                                        for bz in self._bounded_range(min_z,max_z,32*rz+cz,16):
                                            for bx in self._bounded_range(min_x,max_x,32*rx+cx,16):
                                                index = 256 * by + 16 * bz + bx
                                                new_blocks[index] = {'name': 'minecraft:air'}

                                for cy in common_sections:
                                    # copy in-bounds blocks
                                    new_section = new_chunk_sections[cy]
                                    old_section = old_chunk_sections[cy]

                                    new_blocks = BlockArray.from_nbt(new_section, block_map)
                                    old_blocks = BlockArray.from_nbt(old_section, block_map)

                                    for by in self._bounded_range(min_y,max_y,cy,16):
                                        for bz in self._bounded_range(min_z,max_z,32*rz+cz,16):
                                            for bx in self._bounded_range(min_x,max_x,32*rx+cx,16):
                                                index = 256 * by + 16 * bz + bx
                                                new_blocks[index] = old_blocks[index]

                                ################################################
                                # Handle tile entities, entities, and various tick events
                                for category in (
                                    'Entities',
                                    'TileEntities',
                                    'TileTicks',
                                    'LiquidTicks',
                                ):
                                    NewEntities = []

                                    # Keep anything in bounds in the old chunks
                                    if old_chunk.body.has_path( 'Level.' + category ):
                                        for tile_entity in old_chunk.body.at_path( 'Level.' + category ).value:
                                            if tile_entity.has_path('Pos'):
                                                tile_x = tile_entity.at_path(Pos[0]).value
                                                tile_y = tile_entity.at_path(Pos[1]).value
                                                tile_z = tile_entity.at_path(Pos[2]).value
                                            else:
                                                tile_x = tile_entity.at_path('x').value
                                                tile_y = tile_entity.at_path('y').value
                                                tile_z = tile_entity.at_path('z').value

                                            if (
                                                min_x <= tile_x and tile_x < max_x + 1 and
                                                min_y <= tile_y and tile_y < max_y + 1 and
                                                min_z <= tile_z and tile_z < max_z + 1
                                            ):
                                                NewEntities.append(tile_entity)

                                    # Keep anything out of bounds in the new chunks
                                    if new_chunk.body.has_path( 'Level.' + category ):
                                        for tile_entity in new_chunk.body.at_path( 'Level.' + category ).value:
                                            if tile_entity.has_path('Pos'):
                                                tile_x = tile_entity.at_path(Pos[0]).value
                                                tile_y = tile_entity.at_path(Pos[1]).value
                                                tile_z = tile_entity.at_path(Pos[2]).value
                                            else:
                                                tile_x = tile_entity.at_path('x').value
                                                tile_y = tile_entity.at_path('y').value
                                                tile_z = tile_entity.at_path('z').value

                                            if not (
                                                min_x <= tile_x and tile_x < max_x + 1 and
                                                min_y <= tile_y and tile_y < max_y + 1 and
                                                min_z <= tile_z and tile_z < max_z + 1
                                            ):
                                                NewEntities.append(tile_entity)

                                    if new_chunk.body.has_path( 'Level.' + category ):
                                        if len(NewEntities) == 0:
                                            new_chunk.body.at_path('Level').value.pop( category )
                                        else:
                                            new_chunk.body.at_path( 'Level.' + category ).value = NewEntities
                                    elif len(NewEntities) > 0:
                                        new_chunk.body.at_path('Level').value[ category ] = nbt.TagList( NewEntities )

                                region.save_chunk(chunk)
