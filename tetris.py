import pygame as pg
import random
from pygame import gfxdraw
from collections import deque
import math
import os
import pygame_gui
import pandas as pd
import datetime
import sys
import shutil

# CONSTANTS
TILE_SIZE = 50 # size of one square tile
HORIZONTAL_TILES = 10 # tiles per row
VERTICAL_TILES = HORIZONTAL_TILES * 2 # 1:2 aspect ratio
PLAY_AREA_WIDTH, PLAY_AREA_HEIGHT = TILE_SIZE * HORIZONTAL_TILES, TILE_SIZE * VERTICAL_TILES
WINDOW_WIDTH, WINDOW_HEIGHT = PLAY_AREA_WIDTH + TILE_SIZE*6, PLAY_AREA_HEIGHT
BLOCK_LIST = ["I", "O", "T", "L", "J", "S", "Z"] # BLOCK_LIST = ["I", "O", "T", "L", "J", "S", "Z"]
LINE_SCORE_MAP = {1: 100, 2: 300, 3: 500, 4: 800}

# CLASSES
class Tile(pg.sprite.Sprite):
    '''each identical constituent of a block as a sprite'''

    width, height = TILE_SIZE, TILE_SIZE # square tile
    border_thickness = 1
    border_color = (0,0,0,255)
    ghost_tile_color = (0,0,0,30)
    default_surf = pg.Surface((width, height), pg.SRCALPHA)
    inner_rect = pg.Rect(border_thickness, border_thickness, width-(border_thickness*2), height-(border_thickness*2))

    def __init__(self, color, isGhost=False):
        pg.sprite.Sprite.__init__(self)
        self.image = self.default_surf.copy()
        self.rect = self.image.get_rect()
        self.image.fill(self.border_color if not isGhost else color) # this is the border color
        self.image.fill(color if not isGhost else self.ghost_tile_color, rect=self.inner_rect) # fill inner rect with this color
        self.blink_frame = 0.0
        self.offset_from_block_center = pg.math.Vector2(0,0) # each tile's offset/direction vector from its block's center

    def rotate_position_angle(self, block_center, direction): # used for 90deg rotation
        self.offset_from_block_center.rotate_ip(90 if direction else -90) # rotate vector
        rotated_pos = block_center + self.offset_from_block_center # get new position of tile
        self.rect.center = (int(rotated_pos.x), int(rotated_pos.y)) # reposition tile at new position / move rect (rotate)
        self.image = pg.transform.rotate(self.image, -90 if direction else 90) # rotate visual of tile about tile's own center

    def blink(self, dt):
        blink_speed = 1.5 # fps

        # Continuous frame advancing (uses float and has fractional)
        # if 1fps speed, frame goes from 0.00->0.50->1.00 in second
        self.blink_frame += blink_speed * dt 

        # fade out only
        if self.blink_frame >= 1.0: self.blink_frame = 0.0 # restart cycle
        alpha = round(255 * (1.0 - self.blink_frame))

        # 0 --fade in--> 1 --fade out--> 2 (fade in 1 frame, fade out 1 frame)
        # if self.blink_frame >= 2.0: self.blink_frame = 0.0 # restart cycle
        # if self.blink_frame <= 1.0: progress = self.blink_frame
        # else: progress = 2.0 - self.blink_frame
        # alpha = round(255 * progress)

        self.image.set_alpha(alpha)

class BlockGroup(pg.sprite.Group):
    ''' 
    take block type as input, construct a block in its custom shape using Tile class to instantiate multiple tiles
    group can only contain sprites, those sprites have RECT and IMAGE, which can be manipulated
    any method has to be done on each of the sprites individually (using for loop)
    '''
    def __init__(self, type):
        self.blockType = type
        self.cumulative_drop_step = 0
        super().__init__() # call the constructor of the parent group (pygame.sprite.Group), inherits parent's init
        if self.blockType == "I": # construct the unique block with multiple tiles
            self.color = "cyan"
            self.block_center = pg.math.Vector2(TILE_SIZE*2, TILE_SIZE*0.5)
            self.block_rotation_offsets = ((("right",0.5),("down",0.5)),(("up",0),("up",0)),(("left",0.5),("down",0.5)),(("up",0),("up",0))) # 4 states (vertical right, horizontal-no offset, vertical right, horizontal-no offset)
            self.idxRotation = 0

            # first tile
            tile = Tile(self.color)
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE*1.5, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # second tile
            tile = Tile(self.color)
            tile.rect.x += TILE_SIZE * 1 # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE*0.5, 0)
            self.add(tile) # directly add tile into this group instance

            # third tile
            tile = Tile(self.color)
            tile.rect.x += TILE_SIZE * 2 # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE*0.5, 0)
            self.add(tile) # directly add tile into this group instance

            # fourth tile
            tile = Tile(self.color)
            tile.rect.x += TILE_SIZE * 3 # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE*1.5, 0)

            # redraw last tile to ensure uniform black border
            # tile.image.fill(tile.border_color) # erase default inner rect color
            # tile.inner_rect.width -= tile.border_thickness # modify inner rect width to show right border
            # tile.image.fill(self.color, rect=tile.inner_rect)
            
            self.add(tile) # directly add tile into this group instance

            for _ in range(3): self.move("right") # shift spawn point of block

        elif self.blockType == "O":
            self.color = "yellow"
            self.block_center = pg.math.Vector2(TILE_SIZE, TILE_SIZE)

            # first tile
            tile = Tile(self.color)
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE*0.5, -TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # second tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, 0) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE*0.5, -TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # third tile
            tile = Tile(self.color)
            tile.rect.move_ip(0, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE*0.5, TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # fourth tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE*0.5, TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            for _ in range(4): self.move("right") # shift spawn point of block

        elif self.blockType == "T":
            self.color = "purple"
            self.block_center = pg.math.Vector2(TILE_SIZE*1.5, TILE_SIZE*1.5)

            # first tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, 0) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, -TILE_SIZE) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # second tile
            tile = Tile(self.color)
            tile.rect.move_ip(0, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # third tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # fourth tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE*2, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            for _ in range(3): self.move("right") # shift spawn point of block

        elif self.blockType == "L":
            self.color = "orange"
            self.block_center = pg.math.Vector2(TILE_SIZE*1.5, TILE_SIZE*1.5)

            # first tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE*2, 0) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE, -TILE_SIZE) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # second tile
            tile = Tile(self.color)
            tile.rect.move_ip(0, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # third tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # fourth tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE*2, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance
        
            for _ in range(3): self.move("right") # shift spawn point of block

        elif self.blockType == "J":
            self.color = "blue"
            self.block_center = pg.math.Vector2(TILE_SIZE*1.5, TILE_SIZE*1.5)

            # first tile
            tile = Tile(self.color)
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE, -TILE_SIZE) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # second tile
            tile = Tile(self.color)
            tile.rect.move_ip(0, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # third tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # fourth tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE*2, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE, 0) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            for _ in range(3): self.move("right") # shift spawn point of block

        elif self.blockType == "S":
            self.color = "green"
            self.block_center = pg.math.Vector2(TILE_SIZE*1.5, TILE_SIZE)
            self.block_rotation_offsets = ((("right",0.5),("down",0.5)),(("up",0),("up",0)),(("left",0.5),("down",0.5)),(("up",0),("up",0))) # 4 states (vertical right, horizontal-no offset, vertical right, horizontal-no offset)
            self.idxRotation = 0

            # first tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, 0) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, -TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # second tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE*2, 0) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE, -TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # third tile
            tile = Tile(self.color)
            tile.rect.move_ip(0, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE, TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # fourth tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            for _ in range(3): self.move("right") # shift spawn point of block

        elif self.blockType == "Z":
            self.color = "red"
            self.block_center = pg.math.Vector2(TILE_SIZE*1.5, TILE_SIZE)
            self.block_rotation_offsets = ((("right",0.5),("down",0.5)),(("up",0),("up",0)),(("left",0.5),("down",0.5)),(("up",0),("up",0))) # 4 states (vertical right, horizontal-no offset, vertical right, horizontal-no offset)
            self.idxRotation = 0

            # first tile
            tile = Tile(self.color)
            tile.offset_from_block_center = pg.math.Vector2(-TILE_SIZE, -TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # second tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, 0) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, -TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # third tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(0, TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            # fourth tile
            tile = Tile(self.color)
            tile.rect.move_ip(TILE_SIZE*2, TILE_SIZE) # manually set position of tile in this block
            tile.offset_from_block_center = pg.math.Vector2(TILE_SIZE, TILE_SIZE*0.5) # vector of block center to tile center
            self.add(tile) # directly add tile into this group instance

            for _ in range(3): self.move("right") # shift spawn point of block

    def move(self, direction, collide_group=None, scaler=1, isRotationOffset=False, isManualDrop=False):
        stepSize = TILE_SIZE * scaler

        # save pre-move tile (used for rollback)
        old_positions = [tile.rect.copy() for tile in self.sprites()]
        old_center = self.block_center.copy()

        if direction == "right":
            for tile in self.sprites(): tile.rect.x += stepSize # move all sprites (tiles) in this block Group
            if not isRotationOffset: self.block_center.x += stepSize
        elif direction == "left":
            for tile in self.sprites(): tile.rect.x -= stepSize
            if not isRotationOffset: self.block_center.x -= stepSize
        elif direction == "down": 
            for tile in self.sprites(): tile.rect.y += stepSize
            if not isRotationOffset: self.block_center.y += stepSize
            if isManualDrop and collide_group and not pg.sprite.groupcollide(self, collide_group, False, False): 
                self.cumulative_drop_step +=1
        elif direction == "up": 
            for tile in self.sprites(): tile.rect.y -= stepSize
            if not isRotationOffset: self.block_center.y -= stepSize
        elif direction == "bottom":
            # run while loop to repeatedly call "down" movement with collision detection
            # use a boolean return to run while loop, terminates upon collision
            while self.move("down", collide_group, isManualDrop=True): pass

        # rollback method (prevents movement if detect collision post movement)
        # can be bypassed by not passing collide_group argument
        if collide_group and pg.sprite.groupcollide(self, collide_group, False, False): 
            # if collision after movement, revert back (tile rects and block center)
            for tile, old_rect in zip(self.sprites(), old_positions): tile.rect = old_rect
            self.block_center = old_center
            return False

        # print(f"Block center (red dot):{self.block_center}")
        return True

    def rotate(self, collide_group=None, direction=1):
        '''
            direction = 1 (rotate right, clockwise), = 0 (rotate left, counter-clockwise)
        '''
        # save pre-rotate tile (used for rollback)
        preRotate_tiles = [] # [(rects,offset vector,images)]
        for tile in self.sprites():
            preRotate_tiles.append((tile.rect.copy(),tile.offset_from_block_center.copy(),tile.image.copy()))
        old_center = self.block_center.copy()

        for tile in self.sprites(): # rotates all tiles about blocks center
            tile.rotate_position_angle(self.block_center, direction)

        # apply offsets to maintain in grid, and custom cyclic patterns (doesn't account for collisions)
        if self.blockType == "I" or self.blockType == "S" or self.blockType == "Z":
            offset_x = self.block_rotation_offsets[self.idxRotation][0]
            offset_y = self.block_rotation_offsets[self.idxRotation][1]
            self.move(offset_x[0], scaler=offset_x[1], isRotationOffset=True) # move without including collide_group (no rollback)
            self.move(offset_y[0], scaler=offset_y[1], isRotationOffset=True)
            self.idxRotation = self.idxRotation + (1 if direction else -1)
            self.idxRotation = self.idxRotation % (len(self.block_rotation_offsets))

        # ---after doing normal rotation + offsets(if any)---
        # Clamping + Rollback method for block rotation near walls and other blocks ("wall kick")
        if collide_group:
            ref = pg.sprite.groupcollide(self, collide_group, False, False)

            # check where the merging occurs
            # compare block's collided tile coordinates to block center (block center will never merge?)
            if ref: 
                print(f"\n{len(ref)} tiles merged during rotation.")
                max_x_diff, max_y_diff = 0, 0
                for tile in ref:
                    # print(f"tile:{tile}, tile center:{tile.rect.center[0]},{tile.rect.center[1]}, block center:{int(self.block_center.x)},{int(self.block_center.y)}")

                    x_diff = tile.rect.center[0] - self.block_center.x
                    y_diff = tile.rect.center[1] - self.block_center.y
                    # print(f"x_diff: {x_diff}, y_diff: {y_diff}")

                    # among all collided tiles,
                    max_x_diff = min(x_diff, max_x_diff) if (x_diff <= 0 and max_x_diff <= 0) else max(x_diff, max_x_diff) # find the max x_diff 
                    max_y_diff = min(y_diff, max_y_diff) if (y_diff <= 0 and max_y_diff <= 0) else max(y_diff, max_y_diff) # find the max y_diff
                    # print(f"max_x_diff: {max_x_diff}, max_y_diff: {max_y_diff}")

                # then find max_diff, this is the one to refer for direction, max_diff = (value, isX)
                if abs(max_x_diff) > abs(max_y_diff): max_diff = (max_x_diff, True) 
                elif abs(max_x_diff) < abs(max_y_diff): max_diff = (max_y_diff, False)
                elif abs(max_x_diff) == abs(max_y_diff): # need to explore two directions
                    max_diff = ([max_x_diff, max_y_diff], None) # isX = None (meaning take both x and y)

                # print(f"isX: {max_diff[1]}")

                def explore_clamp(clamp_move_direction):
                    nonlocal ref
                    for _ in range(2): # at most 2 blocks merge, move this amount, and break early if no collision detection 
                        self.move(clamp_move_direction)
                        ref = pg.sprite.groupcollide(self, collide_group, False, False)
                        if not ref:
                            print("clamping success")
                            break

                if max_diff[1] is not None: # need to move in one direction only (most cases)
                    # print(f"collision during rotation: {int(max_diff[0])}px from block center in the {"x-axis" if max_diff[1] else "y-axis"}")

                    # once got the direction of collision, I move only in the opposite direction 
                    if max_diff[0] < 0 and max_diff[1]: # collision left
                        print("collision left, attempt moving right")
                        clamp_move_direction = "right"
                    elif max_diff[0] > 0 and max_diff[1]: # collision right
                        print("collision right, attempt moving left")
                        clamp_move_direction = "left"
                    elif max_diff[0] < 0 and not max_diff[1]: # collision top
                        print("collision top, attempt moving down")
                        clamp_move_direction = "down"
                    elif max_diff[0] > 0 and not max_diff[1]: # collision bottom
                        print("collision bottom, attempt moving up")
                        clamp_move_direction = "up"
                    explore_clamp(clamp_move_direction)

                else: # need to explore and move in two directions to see which clears it (cases like L block)
                    first_explore_direction = None
                    # explore left/right first
                    if max_diff[0][0] < 0: # collision left
                        print("collision left, attempt moving right")
                        first_explore_direction = "right"
                    elif max_diff[0][0] > 0: # collision right
                        print("collision right, attempt moving left")
                        first_explore_direction = "left"
                    explore_clamp(first_explore_direction)

                    if ref:
                        # needs to backtrack movement if that direction fails
                        for _ in range(2): 
                            if first_explore_direction == "right": self.move("left")
                            else: self.move("right")

                        # explore top/bottom instead
                        if max_diff[0][1] < 0: # collision top
                            print("collision top, attempt moving down")
                            explore_clamp("down")
                        elif max_diff[0][1] > 0: # collision bottom
                            print("collision bottom, attempt moving up")
                            explore_clamp("up")

            if ref: # if done attempt clamping, and still has collision (ref not empty), do rollback instead
                print("clamping failed, rollback")
                for tile, old_Tile in zip(self.sprites(), preRotate_tiles):
                    tile.rect, tile.offset_from_block_center, tile.image = old_Tile
                self.block_center = old_center

    def blink(self, dt, blink_status=False):
        for tile in self.sprites(): tile.blink(dt) if blink_status else tile.image.set_alpha(255)

class GhostBlock(BlockGroup):
    '''
    take existing BlockGroup object, duplicate its tiles, change its appearance, use parent's move()
    '''
    def generate(self, player_block, collide_group):
        self.empty() # delete default BlockGroup tiles (will create new clone ones next)
        for tile in player_block.sprites():
            tile_clone = Tile(self.color, True) # redraw a new tile with isGhost
            tile_clone.rect.x = tile.rect.x # follow x position of each tile
            tile_clone.rect.y = tile.rect.y # follow y-position of each tile
            self.add(tile_clone) # add all sprites back to "self" group
        self.move("bottom", collide_group) # use parent class method
        return self

class RowScanner(pg.sprite.Sprite):
    '''one sprite the size of one row'''
    def __init__(self):
        width, height = PLAY_AREA_WIDTH, TILE_SIZE
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(0, 0, width, height)
        self.rect.bottom = PLAY_AREA_HEIGHT # initialise at bottom row
        # self.image = pg.Surface((width, height), pg.SRCALPHA)
        # self.image.fill((255, 255, 255, 120))

def get_internal_path(relative_path):
    """ Use for Read-Only files compiled INSIDE the exe (images, audio, gui_theme.json) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def get_writable_csv_path(filename):
    """ Use for the high score CSV file that sits right next to the executable """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.abspath(".")
        
    local_csv_path = os.path.join(exe_dir, filename)
    
    # Deploy an empty template if the user doesn't have the file next to the exe yet
    if not os.path.exists(local_csv_path):
        # We look inside the bundled 'data' folder for the fallback template
        bundled_template = get_internal_path(os.path.join("data", filename))
        if os.path.exists(bundled_template):
            print("exists")
            shutil.copyfile(bundled_template, local_csv_path)
        else:
            # Fallback if you don't use a data folder template: create a blank header file
            with open(local_csv_path, 'w', encoding='utf-8') as f:
                f.write("name,score,level,datetime\n")
            
    return local_csv_path
# main_dir = os.path.split(os.path.abspath(__file__))[0]
def load_sound(file):
    """because pygame can be compiled without mixer."""
    if not pg.mixer:
        return None
    # file = os.path.join(main_dir, "assets", file)
    file = get_internal_path(os.path.join("assets", file))
    try:
        sound = pg.mixer.Sound(file)
        return sound
    except pg.error:
        print(f"Warning, unable to load, {file}")
    return None
def load_image(file):
    """loads an image, prepares it for play"""
    # file = os.path.join(main_dir, "assets", file)
    file = get_internal_path(os.path.join("assets", file))
    try:
        surface = pg.image.load(file)
    except pg.error:
        raise SystemExit(f'Could not load image "{file}" {pg.get_error()}')
    return surface.convert_alpha()

def background(surface):
    # CREATE BACKGROUND
    surface.fill("grey")

    # Draw grid
    grid_color = (200,200,200)
    width, height = PLAY_AREA_WIDTH, PLAY_AREA_HEIGHT
    for x in range(0, width, TILE_SIZE): pg.draw.line(surface, grid_color, (x, 0), (x, height)) # Draw vertical lines
    for y in range(0, height, TILE_SIZE): pg.draw.line(surface, grid_color, (0, y), (width, y)) # Draw horizontal lines

    # Draw title and boundary circle for hold block
    hold_section_center = (PLAY_AREA_WIDTH + TILE_SIZE*3.5, PLAY_AREA_HEIGHT - TILE_SIZE*2.5)
    circle_line_width = 2
    font = pg.font.Font(None, 50) 
    text_surface = font.render("Hold", True, "black")
    text_rect = text_surface.get_rect()
    text_rect.center = (hold_section_center[0], hold_section_center[1] - TILE_SIZE*2.5)
    surface.blit(text_surface, text_rect)
    # pg.draw.circle(surface, "black", hold_section_center, TILE_SIZE*2.2, 2) # pixelated circle
    for a_radius in range(circle_line_width):
        pg.gfxdraw.aacircle(surface, int(hold_section_center[0]), int(hold_section_center[1]), int(TILE_SIZE*2.15) + a_radius, (0,0,0)) # smoother circle (aacircle)

    # Draw title and boundary for next blocks
    next_section_center = (PLAY_AREA_WIDTH + TILE_SIZE*3.5, TILE_SIZE*9)
    font = pg.font.Font(None, 50) 
    text_surface = font.render("Next", True, "black")
    text_rect = text_surface.get_rect()
    text_rect.center = (next_section_center[0], next_section_center[1] - TILE_SIZE*5.5)
    surface.blit(text_surface, text_rect)
    next_boundary_rect = pg.Rect(0, 0, TILE_SIZE*4.5, TILE_SIZE*10)
    next_boundary_rect.center = next_section_center
    pg.draw.rect(surface, "black", next_boundary_rect, 2, border_radius=8)

    # Draw score, level, lines title
    score_level_lines_center = (PLAY_AREA_WIDTH + TILE_SIZE, 10)
    title_font_size = 40
    ref = ["Score: ", "Level: ", "Lines: "]
    for i,item in enumerate(ref):
        font = pg.font.Font(None, title_font_size) 
        text_surface = font.render(item, True, "black")
        text_rect = text_surface.get_rect()
        text_rect.topleft = (score_level_lines_center[0], score_level_lines_center[1] + 50*i)
        surface.blit(text_surface, text_rect)    

def generate_pause_menu(manager):
    pause_window_size = (TILE_SIZE*13, TILE_SIZE*15)
    pause_menu_panel = pygame_gui.elements.UIPanel(
        relative_rect=pg.Rect((0, 0),pause_window_size),
        manager=manager,
        anchors={'center': 'center'}
    )
    pause_menu_headers = pygame_gui.elements.UITextBox(
        html_text=(
            "<font size='7'><b>GAME PAUSED</b></font><br>"
            "<br><br><br><br><br>"
            "<font size='6'><b>CONTROLS</b></font><br>"
            "<br><br><br><br><br><br><br><br><br>"
            "<font size='6'><b>HIGH SCORES</b></font><br>"
        ),
        relative_rect= pg.Rect((0, 0), pause_window_size),
        manager= manager,
        container=pause_menu_panel,
        anchors= {'center': 'center'},
        object_id= pygame_gui.core.ObjectID(class_id='@menu_headers')
    )
    pause_menu_instructions = pygame_gui.elements.UITextBox( 
        html_text=(
            "<font size='5'>Press <b>ESC/P</b> to Continue/Pause Playing</font><br>"
            "<font size='5'>Press <b>R</b> to Restart Game</font><br>"
            "<font size='5'>Press <b>Q</b> to Quit Game</font><br>"
        ),
        relative_rect=pg.Rect((30, 80),(pause_window_size[0], TILE_SIZE * 2)),
        manager=manager,
        container=pause_menu_panel,
        object_id= pygame_gui.core.ObjectID(class_id='@menu_content')
    )
    pause_menu_controls = pygame_gui.elements.UITextBox(
        html_text=(
            "<font size='5'><b>Left Arrow</b>: Move Block Left (Hold for Speed Boost)</font><br>"
            "<font size='5'><b>Right Arrow</b>: Move Block Right (Hold for Speed Boost)</font><br>"
            "<font size='5'><b>Down Arrow</b>: Move Block Down (Hold for Speed Boost)</font><br>"
            "<font size='5'><b>Up Arrow</b>: Rotate Block (Rotate Right / Rotate Clockwise)</font><br>"
            "<font size='5'><b>Z</b>: Rotate Block (Rotate Left / Rotate Counter-Clockwise)</font><br>"
            "<font size='5'><b>Spacebar</b>: Hard Drop / Instant Drop</font><br>"
            "<font size='5'><b>C</b>: Hold/Swap Block</font><br>"
        ),
        relative_rect=pg.Rect((30, 225),(pause_window_size[0], TILE_SIZE * 6)),
        manager=manager,
        container=pause_menu_panel,
        object_id= pygame_gui.core.ObjectID(class_id='@menu_content')
    )
    entry_start_y_pos = 520
    for i, entry in high_scores.head(5).iterrows(): # for top 5 high scores only
        high_score_name = pygame_gui.elements.UILabel(
            text= str(entry['name']),
            relative_rect=pg.Rect((0, entry_start_y_pos + 40*i),(200, 40)),
            manager=manager,
            container=pause_menu_panel,
            anchors={'left':'left'},
            object_id= pygame_gui.core.ObjectID(object_id='#high_score_content')
        )
        high_score = pygame_gui.elements.UILabel(
            text= str(entry['score']) + " (Level " + str(entry['level']) + ")",
            relative_rect=pg.Rect((-10, entry_start_y_pos + 40*i),(170, 40)),
            manager=manager,
            container=pause_menu_panel,
            anchors={'centerx':'centerx'},
            object_id= pygame_gui.core.ObjectID(object_id='#high_score_content')
        )
        high_score_timestamp = pygame_gui.elements.UILabel(
            text= str(entry['datetime']),
            relative_rect=pg.Rect((-230, entry_start_y_pos + 40*i),(220, 40)),
            manager=manager,
            container=pause_menu_panel,
            anchors={'right':'right'},
            object_id= pygame_gui.core.ObjectID(object_id='#high_score_content')
        )

def generate_gameover_menu(manager, cur_score, cur_level, cur_player_name=None, cur_game_over_time=None):
    gameover_window_size = (TILE_SIZE*13, TILE_SIZE*15)
    gameover_menu_panel = pygame_gui.elements.UIPanel(
        relative_rect=pg.Rect((0, 0),gameover_window_size),
        manager=manager,
        anchors={'center': 'center'}
    )
    gameover_menu_headers = pygame_gui.elements.UITextBox(
        html_text=(
            "<font size='7'><b>GAME OVER</b></font><br>"
            "<br><br><br><br><br>"
            "<font size='6'><b>YOUR SCORE</b></font><br>"
            "<br><br><br><br><br><br><br><br><br>"
            "<font size='6'><b>HIGH SCORES</b></font><br>"
        ),
        relative_rect= pg.Rect((0, 0), gameover_window_size),
        manager= manager,
        container=gameover_menu_panel,
        anchors= {'center': 'center'},
        object_id= pygame_gui.core.ObjectID(class_id='@menu_headers', object_id='#gameover_menu_headers')
    )
    gameover_menu_headers.disable() # prevent user from highlighting passive text in textbox
    gameover_menu_instruction = pygame_gui.elements.UITextBox(
        html_text=(
            "<font size='5'>Press <b>R</b> to Restart Game</font><br>"
            "<font size='5'>Press <b>Q</b> to Quit Game</font><br>"
        ),
        relative_rect=pg.Rect((30, 80),(gameover_window_size[0], TILE_SIZE * 2)),
        manager=manager,
        container=gameover_menu_panel,
        object_id= pygame_gui.core.ObjectID(class_id='@menu_content')
    )
    gameover_menu_instruction.disable() # prevent user from highlighting passive text in textbox
    gameover_score_level = pygame_gui.elements.UILabel(
        text= str(cur_score) + " (Level " + str(cur_level) + ")",
        relative_rect=pg.Rect((0, -60),(600, 150)),
        manager=manager,
        container=gameover_menu_panel,
        anchors= {'center': 'center'},
        object_id= pygame_gui.core.ObjectID(object_id='#gameover_score_level')
    )
    gameover_name_entry = pygame_gui.elements.UITextEntryLine(
        relative_rect=pg.Rect((0, 50),(500, 60)),
        manager=manager,
        container=gameover_menu_panel,
        anchors= {'center': 'center'},
        placeholder_text="Enter your name to enter scoreboard..."
    )
    gameover_name_entry.set_text_length_limit(21)

    ref = None
    entry_start_y_pos = 520
    for i, entry in high_scores.head(5).iterrows(): # for top 5 high scores only
        # if current high score made it to top 5, highlight it
        isTopFive = entry['name']==cur_player_name and entry['score']==cur_score and entry['level']==cur_level and entry['datetime']==cur_game_over_time

        object_id_ref = '#high_score_content_current' if isTopFive else '#high_score_content'

        high_score_name = pygame_gui.elements.UILabel(
            text= str(entry['name']),
            relative_rect=pg.Rect((0, entry_start_y_pos + 40*i),(200, 40)),
            manager=manager,
            container=gameover_menu_panel,
            anchors={'left':'left'},
            object_id= pygame_gui.core.ObjectID(object_id=object_id_ref)
        )
        high_score = pygame_gui.elements.UILabel(
            text= str(entry['score']) + " (Level " + str(entry['level']) + ")",
            relative_rect=pg.Rect((-10, entry_start_y_pos + 40*i),(170, 40)),
            manager=manager,
            container=gameover_menu_panel,
            anchors={'centerx':'centerx'},
            object_id= pygame_gui.core.ObjectID(object_id=object_id_ref)
        )
        high_score_timestamp = pygame_gui.elements.UILabel(
            text= str(entry['datetime']),
            relative_rect=pg.Rect((-230, entry_start_y_pos + 40*i),(220, 40)),
            manager=manager,
            container=gameover_menu_panel,
            anchors={'right':'right'},
            object_id= pygame_gui.core.ObjectID(object_id=object_id_ref)
        )

        if isTopFive:
            high_score_name.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)
            ref = (high_score_name, high_score, high_score_timestamp)

    return (gameover_name_entry, gameover_menu_panel, ref)

def countdown_to_play(manager, screen, window):
    start_time = pg.time.get_ticks() / 1000
    current_time = start_time
    current_number = "<effect id=number>3</effect>"
    countdown_number = pygame_gui.elements.UITextBox(
        html_text= current_number,
        relative_rect=pg.Rect((0, 0),(WINDOW_WIDTH, WINDOW_HEIGHT)),
        manager=manager,
        anchors= {'center': 'center'},
        object_id= pygame_gui.core.ObjectID(object_id='#countdown_number')
    )

    # text effects
    # countdown_number.set_active_effect(pygame_gui.TEXT_EFFECT_EXPAND_CONTRACT, params={'time_to_complete_expand_contract': 1.0}, effect_tag="number")
    countdown_number.set_active_effect(pygame_gui.TEXT_EFFECT_FADE_OUT, params={'time_per_alpha_change': 0.005})

    countdown_clock = pg.time.Clock()
    while current_time - start_time < 3.0:
        dt = countdown_clock.tick(60) / 1000.0
        current_time = pg.time.get_ticks() / 1000
        time_passed = current_time - start_time
        if time_passed < 1.0: new_number = "<effect id=number>3</effect>"
        elif time_passed >= 1.0 and time_passed < 2.0: new_number = "<effect id=number>2</effect>"
        elif time_passed >= 2.0 and time_passed < 3.0: new_number = "<effect id=number>1</effect>"
        if new_number != current_number:
            current_number = new_number
            countdown_number.set_text(current_number)
            countdown_number.set_active_effect(pygame_gui.TEXT_EFFECT_FADE_OUT, params={'time_per_alpha_change': 0.005})
        background(screen)
        manager.update(dt)
        manager.draw_ui(screen)
        window.flip()
        # pg.event.get() # get and remove messages from event queue (ignore user inputs during timer countdown, else these messages stay in event queue and carry forward later)
        # pg.event.clear() # same effect as pg.event.get()
        for event in pg.event.get(): # read user input during countdown
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE: # user abort during countdown
                return False 
    return True

def generate_start_menu(manager, bg_image):
    start_window_size = (TILE_SIZE*13, TILE_SIZE*15)
    start_menu_panel = pygame_gui.elements.UIPanel(
        relative_rect=pg.Rect((0, 0),start_window_size),
        manager=manager,
        anchors={'center': 'center'}
    )
    scaled_bg_image = pg.transform.scale_by(bg_image, 0.3)
    scaled_bg_image.set_alpha(80)
    start_menu_panel.add_background_image(scaled_bg_image)
    
    start_menu_headers = pygame_gui.elements.UITextBox(
        html_text=(
            "<font size='7'><b>_</b></font><br>"
            "<br><br><br><br><br>"
            "<font size='6'><b>CONTROLS</b></font><br>"
            "<br><br><br><br><br><br><br><br><br>"
            "<font size='6'><b>HIGH SCORES</b></font><br>"
        ),
        relative_rect= pg.Rect((0, 0), start_window_size),
        manager= manager,
        container=start_menu_panel,
        anchors= {'center': 'center'},
        object_id= pygame_gui.core.ObjectID(class_id='@menu_headers')
    )
    start_menu_headers.disable() # prevent user from highlighting passive text in textbox
    start_game_button = pygame_gui.elements.UIButton(
    relative_rect=pg.Rect((0, 30),(400, 150)),
    text= "START GAME",
    manager=manager,
    container=start_menu_panel,
    anchors={'centerx': 'centerx'},
    object_id= pygame_gui.core.ObjectID(object_id='#start_button')
)
    start_menu_controls = pygame_gui.elements.UITextBox(
        html_text=(
            "<font size='5'><b>Left Arrow</b>: Move Block Left (Hold for Speed Boost)</font><br>"
            "<font size='5'><b>Right Arrow</b>: Move Block Right (Hold for Speed Boost)</font><br>"
            "<font size='5'><b>Down Arrow</b>: Move Block Down (Hold for Speed Boost)</font><br>"
            "<font size='5'><b>Up Arrow</b>: Rotate Block (Rotate Right / Rotate Clockwise)</font><br>"
            "<font size='5'><b>Z</b>: Rotate Block (Rotate Left / Rotate Counter-Clockwise)</font><br>"
            "<font size='5'><b>Spacebar</b>: Hard Drop / Instant Drop</font><br>"
            "<font size='5'><b>C</b>: Hold/Swap Block</font><br>"
        ),
        relative_rect=pg.Rect((30, 225),(start_window_size[0], TILE_SIZE * 6)),
        manager=manager,
        container=start_menu_panel,
        object_id= pygame_gui.core.ObjectID(class_id='@menu_content')
    )
    start_menu_controls.disable() # prevent user from highlighting passive text in textbox
    entry_start_y_pos = 520
    for i, entry in high_scores.head(5).iterrows(): # for top 5 high scores only
        high_score_name = pygame_gui.elements.UILabel(
            text= str(entry['name']),
            relative_rect=pg.Rect((0, entry_start_y_pos + 40*i),(200, 40)),
            manager=manager,
            container=start_menu_panel,
            anchors={'left':'left'},
            object_id= pygame_gui.core.ObjectID(object_id='#high_score_content')
        )
        high_score = pygame_gui.elements.UILabel(
            text= str(entry['score']) + " (Level " + str(entry['level']) + ")",
            relative_rect=pg.Rect((-10, entry_start_y_pos + 40*i),(170, 40)),
            manager=manager,
            container=start_menu_panel,
            anchors={'centerx':'centerx'},
            object_id= pygame_gui.core.ObjectID(object_id='#high_score_content')
        )
        high_score_timestamp = pygame_gui.elements.UILabel(
            text= str(entry['datetime']),
            relative_rect=pg.Rect((-230, entry_start_y_pos + 40*i),(220, 40)),
            manager=manager,
            container=start_menu_panel,
            anchors={'right':'right'},
            object_id= pygame_gui.core.ObjectID(object_id='#high_score_content')
        )
    return start_game_button

def weighted_random(recent):
    '''use weighted random (change probability based on recency) to increase perceived randomness'''
    numbers = list(range(0, len(BLOCK_LIST)))
    weights = [] # list of weights/probabilities for each choice of number
    for n in numbers:
        if n == recent[-1] if recent else False:
            weight = 0.1
        elif n in recent:
            weight = 0.5
        else:
            weight = 1.0
        weights.append(weight)

    # print(weights)
    result = random.choices(numbers, weights=weights, k=1)[0]
    recent.append(result)

    if len(recent) > 3: # only consider 3 recents
        recent.pop(0)

    return result 

def main(high_scores, manager):
    # Initialise background
    # pg.display.set_caption("Tetris")
    # screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT)) # set display mode, and creates a surface to draw on
    # background(screen)
    # pg.display.flip()
    window = pg.Window(title="Tetris", size=(WINDOW_WIDTH, WINDOW_HEIGHT))
    screen = window.get_surface()
    tetris_logo = load_image("tetris_logo.png")
    window.set_icon(tetris_logo)
    background(screen)
    window.flip()

    # Initialise GUI, screens for pause menu, gameover menu
    gui_manager = manager
    overlay_screen_bg = pg.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pg.SRCALPHA)
    overlay_screen_bg.fill(pg.Color("#000000D3")) # overlay for blocking screen (for menus, etc.)
    
    # Initialise sprites and groups
    cur_block = pg.sprite.Group() # store the player's block (BlockGroup class)
    cur_block_ghost = pg.sprite.Group()
    boundary_walls = pg.sprite.Group() # create group to store boundary walls as sprites
    top_wall = pg.sprite.Group()
    for i in range(int(PLAY_AREA_HEIGHT/TILE_SIZE)): # create left and right boundary walls
        tile, tile_mirrored = Tile("black"), Tile("darkgrey")
        tile.rect.y += i * TILE_SIZE # for each row
        tile_mirrored.rect.y += i * TILE_SIZE # for each row
        tile.rect.width *= 2 # thicken wall
        tile_mirrored.rect.width *= 2
        tile.rect.right, tile_mirrored.rect.left = 0, PLAY_AREA_WIDTH # move it out of screen
        boundary_walls.add(tile, tile_mirrored) # (left, right)
    for i in range(int(PLAY_AREA_WIDTH/TILE_SIZE)): # create top and bottom boundary walls
        tile, tile_mirrored = Tile("black"), Tile("black")
        tile.rect.x += i * TILE_SIZE # for each column
        tile_mirrored.rect.x += i * TILE_SIZE # for each column
        tile.rect.height *= 2 # thicken wall
        tile_mirrored.rect.height *= 2
        tile.rect.bottom = 0
        tile_mirrored.rect.top = PLAY_AREA_HEIGHT # move it out of screen
        # boundary_walls.add(tile, tile_mirrored) # (top, bottom)
        boundary_walls.add(tile_mirrored) # bottom
        top_wall.add(tile) # top
    set_Blocks_Walls = pg.sprite.Group(boundary_walls) # stores boundary walls and set/resolved blocks as sprites
    row_scanner = RowScanner()
    cleared_sprites = pg.sprite.Group()
    queue_blocks = pg.sprite.Group()
    hold_block = pg.sprite.Group()

    # Initialise some variables before main loop
    running = True
    isGamePaused = False
    last_move_time = 0
    last_keydown_time = 0
    move_key_held = False
    key_hold_time = 0
    speed_boost_hold_delay = 250 # threshold time to hold movement keys to activate speed boost
    speed_boost_move_delay = 25 # determines speed of speed boosted movement
    fallingEnabled = True
    fall_delay = 1000 # default 1000ms, reduce for higher difficulty
    last_fall_time = 0
    instantTD = False
    timed_touchdown_timeout = 500 # default 500ms, reduce for higher difficulty
    last_collide_time = 0
    ghostEnabled = True
    ghost_connected = False
    cumulative_collide_time = 0
    last_disconnect_time = 0
    cumulative_reset_timeout = 1000
    isTouchdown = False
    autoSpawnEnabled = True
    isAnimateClearing = False
    clear_animation_timer = 0
    clear_animation_duration = 25  # frames
    isLineCleared = False
    idx_cleared_rows = set()
    idxBlock = 0
    idxHold = None
    isHoldBlock = False
    isHoldPressed = False
    level = 1
    score = 0
    total_lines_cleared = 0
    recent_random_idxBlock = []

    # Initialise next block queue with three blocks
    idx_next_block_queue = deque()
    for i in range(3): idx_next_block_queue.append(random.randint(0, len(BLOCK_LIST)-1))

    # Start menu with start game button
    isStartGame = False
    start_menu_clock = pg.time.Clock()
    screen.blit(overlay_screen_bg)
    start_button = generate_start_menu(gui_manager, tetris_logo)
    while not isStartGame:
        dt = start_menu_clock.tick(60) / 1000.0
        for event in pg.event.get(): 
            gui_manager.process_events(event)
            if (event.type == pg.KEYDOWN and event.key == pg.K_q) or event.type == pg.QUIT:
                print("Quit Game")
                return False
            if (event.type == pg.KEYDOWN and event.key == pg.K_p) or (event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element == start_button): # user press P or click start game button
                print("Game Started")
                gui_manager.clear_and_reset() # clear old elements (e.g. from pause menu)
                pg.time.wait(500)
                isCountdownDone = countdown_to_play(gui_manager, screen, window) # 3-second countdown before playing
                if not isCountdownDone: isGamePaused = True
                isStartGame = True
        gui_manager.update(dt)
        gui_manager.draw_ui(screen)
        window.flip()
    background(screen)
    window.flip()
    
    # MAIN LOOP
    clock = pg.time.Clock()
    while running:
        dt = clock.tick(60) / 1000.0 # limits FPS to 60, also compute time passed (dt) for framerate-independent animation use

        # POLL FOR EVENTS / HANDLE PLAYER INPUT (single presses)
        for event in pg.event.get(): 
            if event.type == pg.QUIT: # click X
                return False
            if (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE) or (event.type == pg.KEYDOWN and event.key == pg.K_p) or not window.focused:
                isGamePaused = True

            '''
            if event.type == pg.KEYDOWN and event.key == pg.K_TAB: # manually spawn block group / cycle block
                cur_block = BlockGroup(BLOCK_LIST[idxBlock])
                idxBlock = (idxBlock + 1) % len(BLOCK_LIST)
            if event.type == pg.KEYDOWN and event.key == pg.K_1: cur_block = BlockGroup(BLOCK_LIST[0])
            if event.type == pg.KEYDOWN and event.key == pg.K_2: cur_block = BlockGroup(BLOCK_LIST[1])
            if event.type == pg.KEYDOWN and event.key == pg.K_3: cur_block = BlockGroup(BLOCK_LIST[2])
            if event.type == pg.KEYDOWN and event.key == pg.K_4: cur_block = BlockGroup(BLOCK_LIST[3])
            if event.type == pg.KEYDOWN and event.key == pg.K_5: cur_block = BlockGroup(BLOCK_LIST[4])
            if event.type == pg.KEYDOWN and event.key == pg.K_6: cur_block = BlockGroup(BLOCK_LIST[5])
            if event.type == pg.KEYDOWN and event.key == pg.K_7: cur_block = BlockGroup(BLOCK_LIST[6])
            if event.type == pg.KEYDOWN and event.key == pg.K_f:
                fallingEnabled = not(fallingEnabled)
                print(f"Falling: {"On" if fallingEnabled else "Off"}")
            if event.type == pg.KEYDOWN and event.key == pg.K_g: 
                ghostEnabled = not(ghostEnabled)
                print(f"Ghost: {"On" if ghostEnabled else "Off"}")
            if event.type == pg.KEYDOWN and event.key == pg.K_s: 
                autoSpawnEnabled = not(autoSpawnEnabled)
                print(f"Auto Spawn: {"On" if autoSpawnEnabled else "Off"}")
            '''
                
            if not isAnimateClearing:
                if event.type == pg.KEYDOWN and event.key == pg.K_LEFT: cur_block.move("left", set_Blocks_Walls) # left stepping
                if event.type == pg.KEYDOWN and event.key == pg.K_RIGHT: cur_block.move("right", set_Blocks_Walls) # right stepping
                if event.type == pg.KEYDOWN and event.key == pg.K_DOWN: 
                    cur_block.move("down", set_Blocks_Walls, isManualDrop=True) # down stepping
                    score += cur_block.cumulative_drop_step * 1
                    cur_block.cumulative_drop_step = 0
                    last_fall_time = current_time # reset last fall time, to isolate "falling" from "user pressing down"
                if event.type == pg.KEYDOWN and event.key == pg.K_UP: # rotate block 90 deg (rotate right)
                    if cur_block: cur_block.rotate(set_Blocks_Walls)
                    if pg.mixer and rotate_sound is not None: rotate_sound.play()
                if event.type == pg.KEYDOWN and event.key == pg.K_z: # rotate block 90 deg (rotate left)
                    if cur_block: cur_block.rotate(set_Blocks_Walls, direction=0)
                    if pg.mixer and rotate_sound is not None: rotate_sound.play()
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE: # snap to bottom
                    if cur_block: 
                        cur_block.move("bottom", set_Blocks_Walls, isManualDrop=True)
                        score += cur_block.cumulative_drop_step * 2
                        cur_block.cumulative_drop_step = 0
                        instantTD = True
                if event.type == pg.KEYDOWN and event.key == pg.K_c: # hold block / swap with held block
                    if not isHoldPressed: # boolean that resets when touchdown (prevent swapping more than once before setting current block)
                        if pg.mixer and hold_sound is not None: hold_sound.play()
                        if idxHold is not None: # swap hold with cur 
                            ref = idxBlock
                            idxBlock = idxHold 
                            idxHold = ref
                        else: # put first hold block
                            cur_block.empty() # empty, so will get new block from next queue
                            idxHold = idxBlock
                        isHoldBlock = True
                        isHoldPressed = True

        # Pause/Play Game
        if isGamePaused:
            print("Game Paused")
            gui_manager.clear_and_reset()
            screen.blit(overlay_screen_bg)
            generate_pause_menu(gui_manager)
            gui_manager.update(dt)
            gui_manager.draw_ui(screen)
            window.flip()
            isPausePolling = True
            while isPausePolling:
                for event in pg.event.get():
                    if (event.type == pg.KEYDOWN and event.key == pg.K_q) or event.type == pg.QUIT:
                        print("Quit Game")
                        return False
                    if event.type == pg.KEYDOWN and event.key == pg.K_r:
                        print("Game Restarted")
                        return True
                    if event.type == pg.KEYDOWN and event.key == pg.K_p or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                        print("Game Continued")
                        gui_manager.clear_and_reset() # clear old elements (e.g. from pause menu)
                        isCountdownDone = countdown_to_play(gui_manager, screen, window) # 3-second countdown before playing
                        if isCountdownDone: isGamePaused = False
                        # if countdown interrupted, isGamePaused remains true, let program complete current frame and return here next frame, and trigger pause menu again, while disabling block falling (see below), this allows the background frame of the game to be preserved
                        isPausePolling = False    

        if not isAnimateClearing:
            # HANDLE PLAYER INPUT (continuous presses)
            keys = pg.key.get_pressed() # can read holding presses, simultaneous key presses
            current_time = pg.time.get_ticks() # Manage own timers independent of clock speed

            # speed boost activation for movement key hold
            isMoveKeydown = keys[pg.K_LEFT] or keys[pg.K_RIGHT] or keys[pg.K_DOWN]
            if isMoveKeydown:
                if not move_key_held: 
                    last_keydown_time = current_time # if this is the first keydown, record start time
                    move_key_held = True
                elif move_key_held: key_hold_time = current_time - last_keydown_time # hold time = time passed since first keydown
            else: move_key_held, key_hold_time = False, 0 # key released, reset key_hold_time
            if key_hold_time > speed_boost_hold_delay and cur_block and (current_time - last_move_time > speed_boost_move_delay):
                if keys[pg.K_LEFT]: 
                    cur_block.move("left", set_Blocks_Walls)
                elif keys[pg.K_RIGHT]: # elif for right, so cannot press both left and right simultaneously, will read left first
                    cur_block.move("right", set_Blocks_Walls)
                if keys[pg.K_DOWN]: # normal if for down, so can press left/right + down to move diagonally
                    cur_block.move("down", set_Blocks_Walls, isManualDrop=True)
                    score += cur_block.cumulative_drop_step * 1
                    cur_block.cumulative_drop_step = 0
                    last_fall_time = current_time # reset last fall time, to isolate "falling" from "user pressing down"
                last_move_time = current_time

            # GAME LOGIC
            # create/update ghost block
            if ghostEnabled and cur_block:
                cur_block_ghost = GhostBlock(cur_block.blockType) # need to create an object (with argument for the parent class)
                cur_block_ghost = cur_block_ghost.generate(cur_block, set_Blocks_Walls)
            elif not ghostEnabled: cur_block_ghost.empty()

            # block falling
            fall_delay = round((1.7 * math.exp(-0.3 * level)) * 1000) # fall delay reduces exponentially with level
            # print(f"Fall Delay: {fall_delay} ms")
            if not isGamePaused and fallingEnabled and current_time - last_fall_time > fall_delay:
                if cur_block: cur_block.move("down", set_Blocks_Walls)
                last_fall_time = current_time

            if cur_block: cur_block.blink(dt, False) # normally, set cur_block with default appearance

            if instantTD: # instantly set block
                print("instant touchdown")
                isTouchdown = True
                instantTD = False

            else: # set block upon timer lapsed
                isCollide = pg.sprite.groupcollide(cur_block, cur_block_ghost, False, False)
                if isCollide and len(isCollide) == len(cur_block): # length must match for full coincide
                    if not ghost_connected:
                        if cumulative_collide_time == 0: print("block fully coincide with ghost (initial contact)")
                        ghost_connected = True
                        last_collide_time = current_time # start time

                    # if actively colliding, check default timer (where player doesn't move/rotate) or cumulative timer (where player does move/rotate), whichever lapsed, trigger RESOLVE
                    # cumulative timer only has value if the player move/rotate after initial collide
                    elif (current_time - last_collide_time > timed_touchdown_timeout) or (cumulative_collide_time > timed_touchdown_timeout * 2.7): # can fine-tune added time for player to rotate more and avoid touchdown
                        print("timer lapsed touchdown")
                        isTouchdown = True
                        ghost_connected, cumulative_collide_time = False, 0 # resolve collision, so reset these two

                    cur_block.blink(dt, True) # blink cur_block upon full coincide

                # no longer colliding, but ghost_connected still true, meaning collision unresolved, block move/rotate out of ghost
                elif ghost_connected: 
                    # cum_time += time elapsed since stop colliding = current_time - start_time
                    cumulative_collide_time += current_time - last_collide_time # accumulate time lapsed since it was connected
                    print(f"cumulative_collide_time: {cumulative_collide_time}")
                    last_disconnect_time = current_time # record time when it last disconnected after connecting
                    # print(f"last_disconnect_time: {last_disconnect_time}")
                    ghost_connected = False # set this to false, so that ghost can reconnect later

                elif current_time - last_disconnect_time > cumulative_reset_timeout:
                    cumulative_collide_time = 0 # block moved out of ghost long enough, reset cumulative

            if isTouchdown:
                if pg.mixer and touchdown_sound is not None: touchdown_sound.play()

                # check game over conditions after touchdown, so player has chance to escape
                game_over_condition_1 = pg.sprite.groupcollide(cur_block, set_Blocks_Walls, False, False)
                game_over_condition_2 = pg.sprite.groupcollide(cur_block, top_wall, False, False)
                if game_over_condition_1 or game_over_condition_2:
                    if game_over_condition_1: print("Game Over (Blocked Spawn)")
                    if game_over_condition_2: print("Game Over (Lock Out)")
                    if pg.mixer and game_over_sound is not None: game_over_sound.play()

                    # game over screen
                    screen.blit(overlay_screen_bg)
                    gui_manager.clear_and_reset() # clear old elements (e.g. from pause menu)
                    gameover_name_entry,gameover_menu_panel,_ = generate_gameover_menu(gui_manager, score, level) # generate new ones for game over screen
                    game_over_time = datetime.datetime.now().strftime("%#d-%b-%Y %#I:%M%p")
                    high_score_name_label, high_score_label, high_score_timestamp_label = None, None, None
                    name_done, score_done, timestamp_done = False, False, False
                    label_effect_timer = 0.0
                    label_effect_delay = 3.0
                    while True: # within game over screen, poll user next action (quit, restart, enter name)
                        dt = clock.tick(60) / 1000.0 # gui updates require its own running dt
                        label_effect_timer += dt
                        # print(gameover_name_entry.is_focused)
                        # print(gui_manager.get_focus_set())
                        for event in pg.event.get():
                            gui_manager.process_events(event)

                            # must separate typing and not typing (not typing has keys that restart/quit)
                            if gameover_name_entry.is_focused or event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED: # user is typing
                                if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED: # if user hit enter after typing
                                    print(f"User submitted text: {event.text}")
                                    player_name = event.text

                                    # save new high score to dataframe, sort, then save high scores to file
                                    high_scores.loc[len(high_scores)] = [player_name, score, level, game_over_time]
                                    high_scores.sort_values(by="score", ascending=False, inplace=True, ignore_index=True)
                                    high_scores.to_csv(get_writable_csv_path("tetris_high_scores.csv"), index=False)

                                    # update gameover screen high scores
                                    gui_manager.clear_and_reset() # clear old elements
                                    gameover_name_entry,gameover_menu_panel,cur_top_five = generate_gameover_menu(gui_manager, score, level, player_name, game_over_time)
                                    if cur_top_five: high_score_name_label, high_score_label, high_score_timestamp_label = cur_top_five

                                    # prevent user re-entry
                                    gameover_name_entry.set_text("Score recorded...")
                                    gameover_name_entry.disable()

                                if event.type == pg.QUIT: # user still can click quit during typing
                                    print("Quit Game")
                                    return False

                                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE: # alternate key to unfocus typing
                                    gui_manager.set_focus_set(gameover_menu_panel)
                                        
                            else: # user stopped typing
                                if (event.type == pg.KEYUP and event.key == pg.K_q) or event.type == pg.QUIT:
                                    print("Quit Game")
                                    return False
                                if event.type == pg.KEYUP and event.key == pg.K_r:
                                    print("Game Restarted")
                                    return True
                                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                                    gui_manager.set_focus_set(gameover_name_entry)
                                if event.type == pygame_gui.UI_TEXT_EFFECT_FINISHED:
                                    if event.ui_element == high_score_name_label: name_done = True
                                    elif event.ui_element == high_score_label: score_done = True
                                    elif event.ui_element == high_score_timestamp_label: 
                                        timestamp_done = True
                                        label_effect_timer = 0.0

                            if not gameover_name_entry.is_enabled: # prevent focusing on text entry bar (after disabling post-entry)
                                gui_manager.set_focus_set(gameover_menu_panel)

                        # sequence and loop label effect after delay
                        if name_done:
                            high_score_label.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)
                            name_done = False
                        if score_done:
                            high_score_timestamp_label.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)
                            score_done = False
                        if timestamp_done and label_effect_timer >= label_effect_delay:
                            high_score_name_label.set_active_effect(pygame_gui.TEXT_EFFECT_TYPING_APPEAR)
                            timestamp_done = False

                        gui_manager.update(dt)
                        gui_manager.draw_ui(screen)
                        window.flip()

                # resolve current block (set it and clear it)
                cur_block.blink(dt, False) # revert to default appearance upon setting
                set_Blocks_Walls.add(cur_block)
                cur_block.empty()
                cur_block_ghost.empty()

                # line clearing
                i = 0
                scan_target = VERTICAL_TILES
                isStreak = False
                row_scanner.rect.bottom = PLAY_AREA_HEIGHT # scan starting from bottom
                while i < scan_target: # scan all rows for complete lines
                    # print(i)
                    row_sprites = pg.sprite.spritecollide(row_scanner, set_Blocks_Walls, False)
                    if len(row_sprites) == HORIZONTAL_TILES:
                        if not isStreak:
                            # print(f"row {i} cleared, scanning next 3 rows to check for streak")
                            isStreak = True
                            scan_target = i+4 # scan 3 more times (since one row cleared, and most is 4 in a row)

                        set_Blocks_Walls.remove(row_sprites) # remove the row of sprites (clearing)
                        cleared_sprites.add(row_sprites) # add sprites to group for clearing animation use
                        idx_cleared_rows.add(i) # used for merging uncleared lines

                    row_scanner.rect.y -= TILE_SIZE # move row_scanner up to next row
                    i += 1

                isTouchdown = False
                isHoldPressed = False # to allow hold button to be pressed next block spawn
                if cleared_sprites: isAnimateClearing = True

                # update score, level, difficulty (after line clearing)
                lines_cleared = len(idx_cleared_rows)
                # print(f"Lines Cleared (with this block): {lines_cleared}")
                if lines_cleared and pg.mixer and line_clear_sound is not None: line_clear_sound.play()
                clear_score = LINE_SCORE_MAP.get(lines_cleared, 0) * level
                score += clear_score
                total_lines_cleared += lines_cleared
                level = (total_lines_cleared // 10) + 1 # +1 due to level start at 1
                if level >= 20: timed_touchdown_timeout = 250

            # merge uncleared lines (after line clearing)
            row_scanner.rect.top = 0 # scan starting from top
            if isLineCleared:
                # print(idx_cleared_rows)
                uncleared_sprites = pg.sprite.Group()
                shift_count = 0
                # start from top, go down row-by-row
                for i in range(VERTICAL_TILES-1, -1, -1):
                    if i in idx_cleared_rows: # if this is a cleared row
                        shift_count += 1

                        # if this is the last row or if next row is uncleared (going from cleared to uncleared)
                        if (i == 0) or (i-1 not in idx_cleared_rows): 
                            # shift pending rows based on shift_count (including this cleared row) and reset        
                            for tile in uncleared_sprites.sprites(): tile.rect.y += TILE_SIZE * shift_count 
                            shift_count = 0

                    else: # if this is a uncleared row
                        # add to group
                        row_sprites = pg.sprite.spritecollide(row_scanner, set_Blocks_Walls, False)
                        uncleared_sprites.add(row_sprites)
                    
                    row_scanner.rect.y += TILE_SIZE # move row_scanner down to next row
                idx_cleared_rows.clear()
                isLineCleared = False
            
            if autoSpawnEnabled:
                if not cur_block: # if current block has set, spawn new block
                    if not isAnimateClearing: # don't spawn block (and its ghost) during clearing animation
                        # popleft from and push to queue
                        idxBlock = idx_next_block_queue.popleft()
                        random_index = weighted_random(recent_random_idxBlock)
                        idx_next_block_queue.append(random_index)
                        cur_block = BlockGroup(BLOCK_LIST[idxBlock])

                        # make new list of queue block objects
                        next_block_queue = []
                        for idx in idx_next_block_queue:
                            next_block_queue.append(BlockGroup(BLOCK_LIST[idx]))

                        # position next block queue at display area
                        queue_blocks.empty()
                        for i, block in enumerate(next_block_queue):
                            if block.blockType == "I" or block.blockType == "O": block.move("left", None, 0.5)
                            block.move("right", None, 9)
                            block.move("down", None, 5)
                            block.move("down", None, i*3)
                            queue_blocks.add(block)

            # Handle block instantiation and position when user press hold/swap block button
            if isHoldBlock: 
                # update current block
                cur_block = BlockGroup(BLOCK_LIST[idxBlock])
                
                # update hold block
                hold_block = BlockGroup(BLOCK_LIST[idxHold])
                if hold_block.blockType == "I" or hold_block.blockType == "O": 
                    hold_block.move("left", None, 0.5)
                    if hold_block.blockType == "I": hold_block.move("down", None, 0.5)
                hold_block.move("right", None, 9)
                hold_block.move("down", None, 16.5)

                isHoldBlock = False
            
        elif isAnimateClearing:
            # animate the cleared lines sprites shrinking
            scale_factor = round((1.0 - clear_animation_timer/clear_animation_duration), 4)

            # create a new list of offset scale factors for size of 10, based on the current scale factor
            scale_factor_10_offset = []
            for i in range(1,11):
                scale_factor_10_offset.append(round((scale_factor * i/10), 4))
            # print(scale_factor_10_offset)

            for i, tile in enumerate(cleared_sprites.sprites()):
                tile_center = tile.rect.center
                # tile.image = pg.transform.scale_by(tile.image, scale_factor)
                tile.image = pg.transform.scale_by(tile.image, scale_factor_10_offset[i % 10])
                tile.rect = tile.image.get_rect(center=tile_center)

            clear_animation_timer += 1

            if clear_animation_timer >= clear_animation_duration:
                clear_animation_timer = 0
                cleared_sprites.empty()
                isAnimateClearing = False
                isLineCleared = True

        # Rendering (draw the scene, only groups can draw)
        background(screen) # clear previous screen
        set_Blocks_Walls.draw(screen)   
        queue_blocks.draw(screen) # want to display next blocks even though clearing
        hold_block.draw(screen)

        # render score, level, lines number
        number_center = (PLAY_AREA_WIDTH + TILE_SIZE, 6)
        number_font_size = 50
        ref = [score, level, total_lines_cleared]
        for i,item in enumerate(ref):
            font = pg.font.Font(None, number_font_size) 
            text_surface = font.render(str(item), True, "black")
            text_rect = text_surface.get_rect()
            text_rect.topleft = (number_center[0] + 90, number_center[1] + number_font_size*i)
            screen.blit(text_surface, text_rect)    
    
        if not isAnimateClearing:
            if ghostEnabled: cur_block_ghost.draw(screen)
            cur_block.draw(screen)
            # pg.draw.circle(screen, "red", (int(cur_block.block_center.x), int(cur_block.block_center.y)), 3) # for seeing where block center of rotation is
        elif isAnimateClearing:
            cleared_sprites.draw(screen)

        # pg.display.flip()
        window.flip()

# call the "main" function if running this script
if __name__ == "__main__":
    if pg.get_sdl_version()[0] == 2: pg.mixer.pre_init(44100, -16, 2, 1024) # sound pre-initialise

    pg.init()

    # Initialise sound
    if pg.mixer and not pg.mixer.get_init():
        print("Warning, no sound")
        pg.mixer = None
    rotate_sound = load_sound("UIClick_UI Click 33_CB Sounddesign_ACTIVATION2.wav")
    hold_sound = load_sound("UIClick_Hand Pop UI Diminished 1_RogueWaves_KawaiiUI.wav")
    touchdown_sound = load_sound("Bluezone_BC0304_retrofuturistic_computer_button_013.wav")
    line_clear_sound = load_sound("UIAlert_Confirm Middle 12_RSCPC_USIN.wav")
    game_over_sound = load_sound("SCIMech_Mech Processed Metal 27_RSCPC_SFEW.wav")

    pg.font.init()
    manager = pygame_gui.UIManager((WINDOW_WIDTH, WINDOW_HEIGHT), theme_path=get_internal_path('config/gui_theme.json'))
    manager.preload_fonts(
        [
            {'name': 'noto_sans', 'point_size': 24, 'style': 'bold', 'antialiased': '1'},
            {'name': 'noto_sans', 'point_size': 48, 'style': 'bold', 'antialiased': '1'},
        ]
    )

    game_running = True
    while game_running:
        print("\n")
        high_scores = pd.read_csv(get_writable_csv_path("tetris_high_scores.csv")) # read high score from saved file
        game_running = main(high_scores, manager)
        manager.clear_and_reset()
    pg.quit()