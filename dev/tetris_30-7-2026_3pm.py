import pygame as pg

# CONSTANTS
TILE_SIZE = 50 # size of one square tile
SCREEN_WIDTH, SCREEN_HEIGHT = TILE_SIZE*10, TILE_SIZE*20
SCREENRECT = pg.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
MOVE_DELAY = 150 # Block movement delay (in milliseconds)

# BLOCK DEFAULT PROFILES CONSTANTS
# color, width, height, spawn position (x,y), (orientation/rotation offsets as a tuple)
BLOCK_I = ("cyan", TILE_SIZE*4, TILE_SIZE, SCREEN_WIDTH/2-TILE_SIZE*2, 0, ((1,-1),(-1,1),(2,-1),(-2,1)))
BLOCK_O = ("yellow", TILE_SIZE*2, TILE_SIZE*2, SCREEN_WIDTH/2-TILE_SIZE, 0, ((0,0),(0,0),(0,0),(0,0)))
BLOCK_LIST = (BLOCK_I, BLOCK_O) # leave trailing comma if single tuple element, e.g. BLOCK_LIST = (BLOCK_I,)

# CLASSES
class Block(pg.sprite.Sprite):
    def __init__(self, block_profile):
        self.color, self.width, self.height, x, y, self.orientation_offsets = block_profile
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.hitbox = self.rect.copy()
        self.idxRotate = 0

    def update_hitbox(self):
        self.hitbox = self.rect.copy()
        self.hitbox.y += 1 # move hitbox down, because I only want the bottom edge as hitbox

    def clamp_move(self, direction, walls_group):
        hit_list = pg.sprite.spritecollide(self, walls_group, False)
        for wall in hit_list:
            if direction == "right": self.rect.right = wall.rect.left
            elif direction == "left": self.rect.left = wall.rect.right
            elif direction == "down": self.rect.bottom = wall.rect.top    

    def move(self, direction, walls_group):
        if direction == "right": self.rect.x += TILE_SIZE
        elif direction == "left": self.rect.x -= TILE_SIZE
        elif direction == "down": self.rect.y += TILE_SIZE
        elif direction == "bottom":
            # step as much as needed, but recursive call move "down", will clamp at each step
            for _ in range(SCREEN_HEIGHT - self.rect.bottom): self.move("down", walls_group)
        self.rect.clamp_ip(SCREENRECT) # maintain within boundary
        self.clamp_move(direction, walls_group) # prevent merging with other blocks
        self.update_hitbox()

    def construct_orientation_profile(self):
        # construct orientation profile based on unpacked orientation offsets during __init__
        # only need to extract the offsets, because width and height is surely swapped for each rotation
        self.orientation_profile = []
        isRotated = True
        for x_offset,y_offset in self.orientation_offsets:
            if isRotated:
                self.orientation_profile.append((self.rect.x + x_offset*TILE_SIZE, self.rect.y + y_offset*TILE_SIZE, self.height, self.width))
                isRotated = False
            else:
                self.orientation_profile.append((self.rect.x + x_offset*TILE_SIZE, self.rect.y + y_offset*TILE_SIZE, self.width, self.height))
                isRotated = True
        self.orientation_profile = tuple(self.orientation_profile)

    def rotate(self, walls_group):
        self.construct_orientation_profile()
        dummy_rect = self.rect.copy() # store pre-rotate rect
        self.rect.update(self.orientation_profile[self.idxRotate])
        if pg.sprite.spritecollideany(self, walls_group):
            self.rect = dummy_rect.copy() # revert rect back (meaning prevent rotation to avoid merging)
        else: # if no collision, proceed to update idxRotate for next rotation, and rotate visual
            self.idxRotate = (self.idxRotate + 1) % len(self.orientation_profile) # cycle between the rotation states       
            self.image = pg.transform.rotate(self.image, 90) # this rotates the "visual"
            self.rect.clamp_ip(SCREENRECT) # maintain within boundary
            self.update_hitbox()

def background(screen):
    # CREATE BACKGROUND
    screen.fill("grey")
    # Draw grid
    color = (200,200,200)
    width, height = SCREEN_WIDTH, SCREEN_HEIGHT
    # Draw vertical lines
    for x in range(0, width, TILE_SIZE):
        pg.draw.line(screen, color, (x, 0), (x, height))
    # Draw horizontal lines
    for y in range(0, height, TILE_SIZE):
        pg.draw.line(screen, color, (0, y), (width, y))

def main():
    # INITIALISE
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # create new surface
    background(screen)
    pg.display.flip() # full screen redraw/update (display initial screen)

    cur_block = None
    cur = pg.sprite.GroupSingle()
    set = pg.sprite.Group()

    # invisible rect as screen/boundary bottom edge for block to collide with
    botEdge_rect = pg.Rect(0, SCREEN_HEIGHT, SCREEN_WIDTH, 1)

    # Initialise some variables before main loop
    clock = pg.time.Clock()
    running = True
    last_move_time = 0
    fall_delay = 800 # default 800ms, reduce for higher difficulty
    last_fall_time = 0
    bottom_delay = 1000
    last_touchdown_time = 0
    instantTD = False
    idxBlock = 0

    # MAIN LOOP
    while running:
        # POLL FOR EVENTS
        for event in pg.event.get(): # for single press actions (prevents spamming/debouncing)
            if event.type == pg.QUIT or event.type == pg.KEYUP and event.key == pg.K_ESCAPE: # click X or press ESC
                pg.quit()
            if event.type == pg.KEYUP and event.key == pg.K_r: # restart
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_UP: # rotate block 90 deg
                if cur_block: cur_block.rotate(set)
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE: # snap to bottom
                if cur_block:
                    cur_block.move("bottom", set)
                    instantTD = True
            if event.type == pg.KEYDOWN and event.key == pg.K_a: # manually spawn block, change block type
                cur_block = Block(BLOCK_LIST[idxBlock])
                cur.add(cur_block)
                idxBlock = (idxBlock + 1) % len(BLOCK_LIST)

        # HANDLE PLAYER INPUT
        keys = pg.key.get_pressed() # can read holding presses, simultaneous key presses

        # Manage own timers independent of clock speed
        current_time = pg.time.get_ticks()

        # allows holding key presses, where timer regulates the speed of spamming / block movement speed
        if current_time - last_move_time > MOVE_DELAY:
            if cur_block:
                # elif instead of if for each keys prevents pressing multiple keys simultaneously
                if keys[pg.K_RIGHT]: cur_block.move("right", set)
                elif keys[pg.K_LEFT]: cur_block.move("left", set)
                elif keys[pg.K_DOWN]: 
                    cur_block.move("down", set)
                    last_fall_time = current_time # reset last fall time, to isolate "falling" from "user pressing down"
                last_move_time = current_time

        # block falling at fixed rate
        if current_time - last_fall_time > fall_delay:
            if cur_block: cur_block.move("down", set)
            last_fall_time = current_time

        # custom callback function to check collision of sprite cur_block's inflated hitbox rect with group sprites
        def check_hitbox_collision(sprite_a, sprite_b):
            # sprite_a is cur_block, sprite_b is the collided sprite from set group
            # by default, it checks for sprite_a's .rect, but here I explicitly use .hitbox rect
            return sprite_a.hitbox.colliderect(sprite_b.rect)

        # if block collides with bottom edge or collides with another set block and small delay has passed, set it in stack
        if cur_block and (pg.sprite.spritecollide(cur_block, set, False, collided=check_hitbox_collision) or cur_block.hitbox.colliderect(botEdge_rect)):
            last_fall_time = current_time # reset last fall time, disabling falling during collision
            if instantTD:
                print("instant touchdown")
                set.add(cur_block)
                cur_block = None
                instantTD = False
            elif current_time - last_touchdown_time > bottom_delay:
                print("fall touchdown")
                set.add(cur_block)
                cur_block = None
                last_touchdown_time = current_time
        else:
            last_touchdown_time = current_time

        if not cur_block: # if current block has set, spawn new block
            cur_block = Block(BLOCK_LIST[idxBlock])
            cur.add(cur_block)
            idxBlock = (idxBlock + 1) % len(BLOCK_LIST)

        background(screen) # clear previous screen

        # draw the scene
        cur.draw(screen) # draw current block
        set.draw(screen) # draw set blocks
        pg.display.flip()
        
        clock.tick(60) # limits FPS to 60

# call the "main" function if running this script
if __name__ == "__main__":
    while True:
        main()