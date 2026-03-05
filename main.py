import pygame
import sys
import math
import os
import sys
import traceback

sys.stderr = open("error_log.txt", "w")
sys.stdout = open("output_log.txt", "w")

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Screen settings
NES_WIDTH = 256
NES_HEIGHT = 240
SCALE = 2
TILE_SIZE = 16
FPS = 60

# Debug settings
DEBUG_INFO = True
SHOW_GRID = False
SHOW_SPRITE_SHEET = False
SHOW_SPRITE_LABELS = False
PREVIEW_SHEET_INDEX = 0

# Physics constants
GRAVITY = 0.4
MAX_FALL_SPEED = 8.0

# Mario physics
MARIO_WALK_ACCEL = 0.1
MARIO_RUN_ACCEL = 0.15
MARIO_RELEASE_DECEL = 0.15
MARIO_SKID_DECEL = 0.25
MARIO_MAX_WALK_SPEED = 1.5
MARIO_MAX_RUN_SPEED = 2.5
MARIO_JUMP_VELOCITY = -6.5
MARIO_JUMP_VELOCITY_RUN = -7.0
MARIO_SMALL_JUMP_CUT = 0.4

# Enemy physics
GOOMBA_SPEED = 0.5
KOOPA_SPEED = 0.7
SHELL_KICK_SPEED = 4.0

# Power-up physics
MUSHROOM_SPEED = 1.2
MUSHROOM_BOUNCE_VELOCITY = -4.0

# Timing constants
INVINCIBILITY_TIME = 10 * FPS
DAMAGE_INVINCIBILITY_TIME = 2 * FPS
BLOCK_BUMP_TIME = 10
DEATH_ANIMATION_TIME = 2 * FPS
STOMP_BOUNCE_VELOCITY = -4.0

# Colors (fallback when textures not available)
COLOR_SKY = (92, 148, 252)
COLOR_GROUND = (0, 168, 0)
COLOR_BRICK = (184, 0, 0)
COLOR_QUESTION = (255, 184, 0)
COLOR_PIPE = (0, 200, 0)
COLOR_MARIO_SMALL = (255, 0, 0)
COLOR_MARIO_SUPER = (255, 100, 0)
COLOR_MARIO_FIRE = (255, 255, 255)
COLOR_GOOMBA = (136, 96, 0)
COLOR_KOOPA_GREEN = (0, 168, 0)
COLOR_KOOPA_RED = (200, 0, 0)
COLOR_SHELL = (0, 100, 200)
COLOR_MUSHROOM = (255, 0, 0)
COLOR_FIRE_FLOWER = (255, 100, 0)
COLOR_STAR = (255, 255, 0)
COLOR_FIREBALL = (255, 200, 0)

# ============================================================================
# GAME INITIALIZATION
# ============================================================================

pygame.init()
screen = pygame.display.set_mode((NES_WIDTH * SCALE, NES_HEIGHT * SCALE))
pygame.display.set_caption("Super Mario Bros (1985) Recreation")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 20)

# ============================================================================
# TEXTURE MANAGER
# ============================================================================

class TextureManager:
    """Manages sprite sheets and texture loading"""
    
    def __init__(self):
        self.sprites = {}
        self.sprite_sheets = []
        self.use_textures = False
        
    def load_sprite_sheet(self, path):
        """Load a sprite sheet from file"""
        try:
            sheet = pygame.image.load(path).convert_alpha()
            self.sprite_sheets.append(sheet)
            self.use_textures = True
            return sheet
        except:
            print(f"Warning: Could not load sprite sheet: {path}")
            return None
    
    def get_sprite(self, sheet_index, x, y, width, height, scale=SCALE):
        """Extract a sprite from a sheet"""
        if sheet_index >= len(self.sprite_sheets):
            return None
        sheet = self.sprite_sheets[sheet_index]
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(sheet, (0, 0), (x, y, width, height))
        scaled = pygame.transform.scale(sprite, (width * scale, height * scale))
        return scaled
    
    def get_sprite_grid(self, sheet_index, grid_x, grid_y, width=16, height=16, border=1, scale=SCALE):
        """Extract a sprite using grid coordinates (accounts for 1px borders and 1px starting offset)"""
        if sheet_index >= len(self.sprite_sheets):
            return None
        # border is added as initial offset since sprites start at (1,1) not (0,0)
        pixel_x = border + grid_x * (width + border)
        pixel_y = border + grid_y * (height + border)
        return self.get_sprite(sheet_index, pixel_x, pixel_y, width, height, scale)
    
    def load_mario_sprites(self):
        """Load all Mario sprites — sheet 0 = 50365.png"""
        if not self.use_textures:
            return
        # Small Mario (row 0, 16x16)
        self.sprites['mario_small_stand'] = self.get_sprite_grid(0, 0, 0, 16, 16)
        self.sprites['mario_small_walk1'] = self.get_sprite_grid(0, 1, 0, 16, 16)
        self.sprites['mario_small_walk2'] = self.get_sprite_grid(0, 2, 0, 16, 16)
        self.sprites['mario_small_jump']  = self.get_sprite_grid(0, 5, 0, 16, 16)
        self.sprites['mario_small_skid']  = self.get_sprite_grid(0, 4, 0, 16, 16)
        # Big Mario (row 1, spans 2 rows height=32)
        self.sprites['mario_super_stand'] = self.get_sprite_grid(0, 0, 1, 16, 32)
        self.sprites['mario_super_walk1'] = self.get_sprite_grid(0, 1, 1, 16, 32)
        self.sprites['mario_super_walk2'] = self.get_sprite_grid(0, 2, 1, 16, 32)
        self.sprites['mario_super_jump']  = self.get_sprite_grid(0, 5, 1, 16, 32)
        self.sprites['mario_super_crouch']= self.get_sprite_grid(0, 6, 1, 16, 32)
        self.sprites['mario_super_skid']  = self.get_sprite_grid(0, 4, 1, 16, 32)
        # Fire Mario (row 3, spans 2 rows height=32)
        self.sprites['mario_fire_stand']  = self.get_sprite_grid(0, 0, 3, 16, 32)
        self.sprites['mario_fire_walk1']  = self.get_sprite_grid(0, 1, 3, 16, 32)
        self.sprites['mario_fire_walk2']  = self.get_sprite_grid(0, 2, 3, 16, 32)
        self.sprites['mario_fire_jump']   = self.get_sprite_grid(0, 5, 3, 16, 32)
        self.sprites['mario_fire_crouch'] = self.get_sprite_grid(0, 6, 3, 16, 32)
        self.sprites['mario_fire_skid']   = self.get_sprite_grid(0, 4, 3, 16, 32)

    def load_block_sprites(self):
        """Load block sprites — sheet 1 = 52570.png"""
        if not self.use_textures:
            return
        self.sprites['ground']        = self.get_sprite_grid(1, 0, 0, 16, 16)
        self.sprites['brick']         = self.get_sprite_grid(1, 1, 0, 16, 16)
        self.sprites['question']      = self.get_sprite_grid(1, 2, 0, 16, 16)
        self.sprites['question_used'] = self.get_sprite_grid(1, 3, 0, 16, 16)
        self.sprites['pipe_ul']       = self.get_sprite_grid(1, 0, 1, 16, 16)
        self.sprites['pipe_ur']       = self.get_sprite_grid(1, 1, 1, 16, 16)
        self.sprites['pipe_ml']       = self.get_sprite_grid(1, 0, 2, 16, 16)
        self.sprites['pipe_mr']       = self.get_sprite_grid(1, 1, 2, 16, 16)

    def load_enemy_sprites(self):
        """Load enemy sprites — sheet 2 = 52572.png"""
        if not self.use_textures:
            return
        self.sprites['goomba_walk1']      = self.get_sprite_grid(2, 0, 0, 16, 16)
        self.sprites['goomba_walk2']      = self.get_sprite_grid(2, 1, 0, 16, 16)
        self.sprites['goomba_stomped']    = self.get_sprite_grid(2, 2, 0, 16, 8)
        self.sprites['koopa_green_walk1'] = self.get_sprite_grid(2, 0, 1, 16, 24)
        self.sprites['koopa_green_walk2'] = self.get_sprite_grid(2, 1, 1, 16, 24)
        self.sprites['koopa_red_walk1']   = self.get_sprite_grid(2, 3, 1, 16, 24)
        self.sprites['koopa_red_walk2']   = self.get_sprite_grid(2, 4, 1, 16, 24)
        self.sprites['shell_green']       = self.get_sprite_grid(2, 0, 3, 16, 16)
        self.sprites['shell_red']         = self.get_sprite_grid(2, 1, 3, 16, 16)

    def load_powerup_sprites(self):
        """Load power-up sprites — sheet 3 = 52574.png"""
        if not self.use_textures:
            return
        self.sprites['mushroom']    = self.get_sprite_grid(3, 0, 0, 16, 16)
        self.sprites['fire_flower'] = self.get_sprite_grid(3, 1, 0, 16, 16)
        self.sprites['star']        = self.get_sprite_grid(3, 2, 0, 16, 16)
        self.sprites['fireball']    = self.get_sprite_grid(3, 3, 0, 8, 8)

    def load_all_sprites(self):
        """Load all sprite sheets in order — index matters!"""
        sheets = [
            r"[TEMP]\50365.png",    # index 0 — Mario characters
            r"[TEMP]\52570.png",    # index 1 — Tiles/blocks
            r"[TEMP]\52572.png",    # index 2 — Enemies
            r"[TEMP]\52574.png",    # index 3 — Power-ups
        ]
        for path in sheets:
            self.load_sprite_sheet(path)  # Load ALL — no break!

        if self.use_textures:
            self.load_mario_sprites()
            self.load_block_sprites()
            self.load_enemy_sprites()
            self.load_powerup_sprites()

# Create the global texture manager instance — must exist before any class uses it
texture_manager = TextureManager()
texture_manager.load_all_sprites()

# ============================================================================
# TILE DEFINITIONS
# ============================================================================

TILE_EMPTY = 0
TILE_GROUND = 1
TILE_BRICK = 2
TILE_QUESTION = 3
TILE_USED_QUESTION = 4
TILE_PIPE_UL = 5
TILE_PIPE_UR = 6
TILE_PIPE_ML = 7
TILE_PIPE_MR = 8
TILE_FLAGPOLE = 9

# ============================================================================
# ENTITY TYPES
# ============================================================================

ENTITY_NONE = 0
ENTITY_GOOMBA = 1
ENTITY_KOOPA_GREEN = 2
ENTITY_KOOPA_RED = 3
ENTITY_MUSHROOM = 4
ENTITY_FIRE_FLOWER = 5
ENTITY_STAR = 6
ENTITY_SHELL = 7
ENTITY_FIREBALL = 8

# ============================================================================
# MARIO STATES
# ============================================================================

MARIO_STATE_SMALL = 0
MARIO_STATE_SUPER = 1
MARIO_STATE_FIRE = 2

# ============================================================================
# LEVEL CLASS
# ============================================================================

class Level:
    """Handles level data, tiles, and rendering"""
    
    def __init__(self, level_data):
        self.tiles = level_data
        self.height = len(level_data)
        self.width = len(level_data[0]) if self.height > 0 else 0
        self.blocks = []
        self.camera_x = 0
        
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                if tile in [TILE_BRICK, TILE_QUESTION]:
                    self.blocks.append(Block(x, y, tile))
    
    def get_tile(self, tile_x, tile_y):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tiles[tile_y][tile_x]
        return TILE_EMPTY
    
    def set_tile(self, tile_x, tile_y, tile_type):
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            self.tiles[tile_y][tile_x] = tile_type
    
    def is_solid(self, tile_x, tile_y):
        tile = self.get_tile(tile_x, tile_y)
        return tile in [TILE_GROUND, TILE_BRICK, TILE_QUESTION, TILE_USED_QUESTION,
                       TILE_PIPE_UL, TILE_PIPE_UR, TILE_PIPE_ML, TILE_PIPE_MR]
    
    def update(self, mario):
        target_camera = mario.x - (NES_WIDTH / 2)
        max_camera = (self.width * TILE_SIZE) - NES_WIDTH
        self.camera_x = max(0, min(target_camera, max_camera))
        
        for block in self.blocks:
            block.update()
    
    def draw(self, surface):
        start_tile_x = int(self.camera_x / TILE_SIZE)
        end_tile_x = start_tile_x + (NES_WIDTH // TILE_SIZE) + 2
        
        block_positions = {(block.tile_x, block.tile_y) for block in self.blocks}
        
        for y in range(self.height):
            for x in range(start_tile_x, min(end_tile_x, self.width)):
                if (x, y) in block_positions:
                    continue
                
                tile = self.get_tile(x, y)
                if tile != TILE_EMPTY:
                    screen_x = (x * TILE_SIZE - self.camera_x) * SCALE
                    screen_y = y * TILE_SIZE * SCALE
                    
                    # Try to use texture first
                    sprite = None
                    if tile == TILE_GROUND:
                        sprite = texture_manager.sprites.get('ground')
                        color = COLOR_GROUND
                    elif tile == TILE_BRICK:
                        sprite = texture_manager.sprites.get('brick')
                        color = COLOR_BRICK
                    elif tile == TILE_QUESTION:
                        sprite = texture_manager.sprites.get('question')
                        color = COLOR_QUESTION
                    elif tile == TILE_USED_QUESTION:
                        sprite = texture_manager.sprites.get('question_used')
                        color = (160, 120, 0)
                    elif tile == TILE_PIPE_UL:
                        sprite = texture_manager.sprites.get('pipe_ul')
                        color = COLOR_PIPE
                    elif tile == TILE_PIPE_UR:
                        sprite = texture_manager.sprites.get('pipe_ur')
                        color = COLOR_PIPE
                    elif tile == TILE_PIPE_ML:
                        sprite = texture_manager.sprites.get('pipe_ml')
                        color = COLOR_PIPE
                    elif tile == TILE_PIPE_MR:
                        sprite = texture_manager.sprites.get('pipe_mr')
                        color = COLOR_PIPE
                    elif tile == TILE_FLAGPOLE:
                        color = (255, 255, 255)
                    else:
                        color = (100, 100, 100)
                    
                    if sprite:
                        surface.blit(sprite, (screen_x, screen_y))
                    else:
                        pygame.draw.rect(surface, color,
                                       (screen_x, screen_y,
                                        TILE_SIZE * SCALE, TILE_SIZE * SCALE))
        
        for block in self.blocks:
            block.draw(surface, self.camera_x)
        
        if SHOW_GRID:
            for x in range(start_tile_x, min(end_tile_x, self.width)):
                screen_x = (x * TILE_SIZE - self.camera_x) * SCALE
                pygame.draw.line(surface, (0, 0, 0),
                               (screen_x, 0), (screen_x, NES_HEIGHT * SCALE))
            for y in range(self.height + 1):
                screen_y = y * TILE_SIZE * SCALE
                pygame.draw.line(surface, (0, 0, 0),
                               (0, screen_y), (NES_WIDTH * SCALE, screen_y))

# ============================================================================
# BLOCK CLASS
# ============================================================================

class Block:
    """Represents interactive blocks (brick, question)"""
    
    def __init__(self, tile_x, tile_y, block_type):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE
        self.type = block_type
        self.bump_timer = 0
        self.bump_offset = 0
        self.contents = ENTITY_NONE
        
        if block_type == TILE_QUESTION:
            import random
            choices = [ENTITY_MUSHROOM, ENTITY_FIRE_FLOWER, ENTITY_STAR]
            self.contents = random.choice(choices)
    
    def hit(self, game, from_bottom=True):
        """Block is hit by Mario from bottom - FIXED: Now bounces properly"""
        if not from_bottom:
            return
        
        if self.type == TILE_BRICK:
            # FIXED: Start bump animation
            self.bump_timer = BLOCK_BUMP_TIME
            
            if game.mario.state != MARIO_STATE_SMALL:
                game.level.set_tile(self.tile_x, self.tile_y, TILE_EMPTY)
                self.bump_timer = 0
                return True
        
        elif self.type == TILE_QUESTION:
            # FIXED: Bump animation for question blocks too
            self.bump_timer = BLOCK_BUMP_TIME
            self.type = TILE_USED_QUESTION
            game.level.set_tile(self.tile_x, self.tile_y, TILE_USED_QUESTION)
            
            if game.mario.state == MARIO_STATE_SMALL:
                game.entities.append(Mushroom(self.x, self.y - TILE_SIZE))
            elif self.contents == ENTITY_MUSHROOM:
                game.entities.append(FireFlower(self.x, self.y - TILE_SIZE))
            elif self.contents == ENTITY_FIRE_FLOWER:
                game.entities.append(FireFlower(self.x, self.y - TILE_SIZE))
            elif self.contents == ENTITY_STAR:
                game.entities.append(Star(self.x, self.y - TILE_SIZE))
        
        return False
    
    def update(self):
        """Update block animation - FIXED"""
        if self.bump_timer > 0:
            self.bump_timer -= 1
            progress = 1.0 - (self.bump_timer / BLOCK_BUMP_TIME)
            # Smoother bounce using sine wave
            self.bump_offset = -8 * math.sin(progress * math.pi)
        else:
            self.bump_offset = 0
    
    def draw(self, surface, camera_x):
        """Draw block with bump animation"""
        screen_x = (self.x - camera_x) * SCALE
        screen_y = (self.y + self.bump_offset) * SCALE
        
        sprite = None
        if self.type == TILE_BRICK:
            sprite = texture_manager.sprites.get('brick')
            color = COLOR_BRICK
        elif self.type == TILE_QUESTION:
            sprite = texture_manager.sprites.get('question')
            color = COLOR_QUESTION
        elif self.type == TILE_USED_QUESTION:
            sprite = texture_manager.sprites.get('question_used')
            color = (160, 120, 0)
        else:
            return
        
        if sprite:
            surface.blit(sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, color,
                            (screen_x, screen_y, TILE_SIZE * SCALE, TILE_SIZE * SCALE))

# ============================================================================
# MARIO CLASS
# ============================================================================

class Mario:
    """The player character"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = 14
        self.height = 16
        self.on_ground = False
        self.state = MARIO_STATE_SMALL
        self.facing_right = True
        self.crouching = False
        self.skidding = False
        self.jumping = False
        self.running = False
        self.invincible = False
        self.invincibility_timer = 0
        self.damage_invincibility_timer = 0
        self.anim_timer = 0
        self.dead = False
        self.death_timer = 0
        self.lives = 3
    
    def update(self, keys, level, entities):
        """Update Mario's physics and state"""
        if self.dead:
            self.death_timer += 1
            self.vy += GRAVITY
            self.y += self.vy
            return
        
        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1
            if self.invincibility_timer == 0:
                self.invincible = False
        
        if self.damage_invincibility_timer > 0:
            self.damage_invincibility_timer -= 1
        
        if self.state == MARIO_STATE_SMALL:
            self.height = 16
        else:
            self.height = 32
        
        if self.state != MARIO_STATE_SMALL and keys[pygame.K_DOWN] and self.on_ground:
            self.crouching = True
        else:
            self.crouching = False
        
        self.running = keys[pygame.K_z]
        
        self.update_horizontal_movement(keys)
        self.update_jumping(keys)
        
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > MAX_FALL_SPEED:
                self.vy = MAX_FALL_SPEED
        
        self.x += self.vx
        self.y += self.vy
        
        self.handle_collision(level, entities)
        
        self.anim_timer += 1
        
        if self.x < level.camera_x:
            self.x = level.camera_x
            self.vx = 0
    
    def update_horizontal_movement(self, keys):
        """Handle horizontal movement and acceleration - FIXED: No wall sticking"""
        if self.crouching:
            if self.vx > 0:
                self.vx -= MARIO_RELEASE_DECEL
                if self.vx < 0:
                    self.vx = 0
            elif self.vx < 0:
                self.vx += MARIO_RELEASE_DECEL
                if self.vx > 0:
                    self.vx = 0
            return
        
        accel = MARIO_RUN_ACCEL if self.running else MARIO_WALK_ACCEL
        max_speed = MARIO_MAX_RUN_SPEED if self.running else MARIO_MAX_WALK_SPEED
        
        if keys[pygame.K_LEFT]:
            if self.vx > 0:
                self.skidding = True
                self.vx -= MARIO_SKID_DECEL
            else:
                self.skidding = False
                self.vx -= accel
                if self.vx < -max_speed:
                    self.vx = -max_speed
            self.facing_right = False
        
        elif keys[pygame.K_RIGHT]:
            if self.vx < 0:
                self.skidding = True
                self.vx += MARIO_SKID_DECEL
            else:
                self.skidding = False
                self.vx += accel
                if self.vx > max_speed:
                    self.vx = max_speed
            self.facing_right = True
        
        else:
            self.skidding = False
            if self.vx > 0:
                self.vx -= MARIO_RELEASE_DECEL
                if self.vx < 0:
                    self.vx = 0
            elif self.vx < 0:
                self.vx += MARIO_RELEASE_DECEL
                if self.vx > 0:
                    self.vx = 0
    
    def update_jumping(self, keys):
        """Handle jumping mechanics"""
        if keys[pygame.K_x] and self.on_ground:
            self.jumping = True
            self.on_ground = False
            if abs(self.vx) > MARIO_MAX_WALK_SPEED:
                self.vy = MARIO_JUMP_VELOCITY_RUN
            else:
                self.vy = MARIO_JUMP_VELOCITY
        
        if not keys[pygame.K_x] and self.jumping and self.vy < 0:
            self.vy *= MARIO_SMALL_JUMP_CUT
            self.jumping = False
    
    def handle_collision(self, level, entities):
        """Handle collision with tiles and entities"""
        self.on_ground = False
        
        collision_height = 16 if self.crouching else self.height
        
        left = int(self.x / TILE_SIZE)
        right = int((self.x + self.width) / TILE_SIZE)
        top = int(self.y / TILE_SIZE)
        bottom = int((self.y + collision_height) / TILE_SIZE)
        
        if self.vy >= 0:
            for x in range(left, right + 1):
                if level.is_solid(x, bottom):
                    tile_top = bottom * TILE_SIZE
                    if self.y + collision_height >= tile_top:
                        self.y = tile_top - collision_height
                        self.vy = 0
                        self.on_ground = True
                        self.jumping = False
                    break
        
        elif self.vy < 0:
            for x in range(left, right + 1):
                if level.is_solid(x, top):
                    self.y = (top + 1) * TILE_SIZE
                    self.vy = 0
                    
                    for block in level.blocks:
                        if block.tile_x == x and block.tile_y == top:
                            block.hit(game, from_bottom=True)
                    break
        
        # FIXED: Removed wall sticking logic - Mario can slide along walls now
        left = int(self.x / TILE_SIZE)
        right = int((self.x + self.width) / TILE_SIZE)
        top = int(self.y / TILE_SIZE)
        bottom = int((self.y + collision_height - 1) / TILE_SIZE)
        
        if self.vx > 0:
            for y in range(top, bottom + 1):
                if level.is_solid(right, y):
                    self.x = right * TILE_SIZE - self.width
                    self.vx = 0
                    break
        
        elif self.vx < 0:
            for y in range(top, bottom + 1):
                if level.is_solid(left, y):
                    self.x = (left + 1) * TILE_SIZE
                    self.vx = 0
                    break
        
        self.handle_entity_collision(entities)
    
    def handle_entity_collision(self, entities):
        """Handle collision with entities - FIXED: Starman kills enemies, shell stomp crash"""
        collision_height = 16 if self.crouching else self.height
        mario_rect = pygame.Rect(self.x, self.y, self.width, collision_height)
        
        for entity in entities[:]:
            if entity.dead:
                continue
            
            if entity.type == ENTITY_GOOMBA and hasattr(entity, 'stomped') and entity.stomped:
                continue
            
            entity_rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
            
            if mario_rect.colliderect(entity_rect):
                # FIXED: Invincibility kills enemies
                if self.invincible and entity.type in [ENTITY_GOOMBA, ENTITY_KOOPA_GREEN, ENTITY_KOOPA_RED, ENTITY_SHELL]:
                    entity.dead = True
                    continue
                
                # Check if stomping enemy
                if (self.vy > 0 and 
                    self.y + collision_height <= entity.y + 8 and
                    entity.type in [ENTITY_GOOMBA, ENTITY_KOOPA_GREEN, ENTITY_KOOPA_RED, ENTITY_SHELL]):
                    
                    # FIXED: Shell stomp handling
                    if entity.type == ENTITY_SHELL:
                        if entity.moving:
                            entity.vx = 0
                            entity.moving = False
                        self.vy = STOMP_BOUNCE_VELOCITY
                    else:
                        entity.stomp(game)  # Pass game instance
                        self.vy = STOMP_BOUNCE_VELOCITY
                
                elif entity.type in [ENTITY_MUSHROOM, ENTITY_FIRE_FLOWER, ENTITY_STAR]:
                    entity.collect(self)
                    entities.remove(entity)
                
                elif entity.type in [ENTITY_GOOMBA, ENTITY_KOOPA_GREEN, ENTITY_KOOPA_RED]:
                    if self.damage_invincibility_timer == 0 and not self.invincible:
                        self.take_damage()
                
                elif entity.type == ENTITY_SHELL:
                    if not entity.moving:
                        entity.kick(self.facing_right)
                        self.vx = -2 if self.facing_right else 2
                    else:
                        if self.damage_invincibility_timer == 0 and not self.invincible:
                            self.take_damage()
    
    def take_damage(self):
        """Take damage (power down or die)"""
        if self.state == MARIO_STATE_FIRE:
            self.state = MARIO_STATE_SUPER
            self.damage_invincibility_timer = DAMAGE_INVINCIBILITY_TIME
        elif self.state == MARIO_STATE_SUPER:
            self.state = MARIO_STATE_SMALL
            self.damage_invincibility_timer = DAMAGE_INVINCIBILITY_TIME
        else:
            self.die()
    
    def die(self):
        """Mario dies"""
        self.dead = True
        self.vy = -8
        self.lives -= 1
    
    def power_up_mushroom(self):
        if self.state == MARIO_STATE_SMALL:
            self.state = MARIO_STATE_SUPER
    
    def power_up_fire_flower(self):
        if self.state == MARIO_STATE_SMALL:
            self.state = MARIO_STATE_SUPER
        else:
            self.state = MARIO_STATE_FIRE
    
    def power_up_star(self):
        self.invincible = True
        self.invincibility_timer = INVINCIBILITY_TIME
    
    def shoot_fireball(self, entities):
        """Shoot a fireball - FIXED: Max 2 fireballs"""
        if self.state == MARIO_STATE_FIRE:
            fireball_count = sum(1 for e in entities if e.type == ENTITY_FIREBALL and not e.dead)
            if fireball_count >= 2:  # FIXED: Changed from 3 to 2
                return
            
            fb_x = self.x + (self.width if self.facing_right else 0)
            fb_y = self.y + self.height / 2
            entities.append(Fireball(fb_x, fb_y, self.facing_right))
    
    def draw(self, surface, camera_x):
        """Draw Mario with sprites"""
        if self.dead:
            screen_x = (self.x - camera_x) * SCALE
            screen_y = self.y * SCALE
            pygame.draw.rect(surface, COLOR_MARIO_SMALL,
                           (screen_x, screen_y, self.width * SCALE, 16 * SCALE))
            return
        
        if self.damage_invincibility_timer > 0 and (self.damage_invincibility_timer // 4) % 2 == 0:
            return
        
        # Get sprite based on state and animation
        sprite = None
        state_prefix = ['mario_small', 'mario_super', 'mario_fire'][self.state]
        
        if not self.on_ground:
            sprite = texture_manager.sprites.get(f'{state_prefix}_jump')
        elif self.crouching:
            sprite = texture_manager.sprites.get(f'{state_prefix}_crouch')
        elif self.skidding:
            sprite = texture_manager.sprites.get(f'{state_prefix}_skid')
        elif abs(self.vx) > 0.1:
            walk_frame = (self.anim_timer // 8) % 2 + 1
            sprite = texture_manager.sprites.get(f'{state_prefix}_walk{walk_frame}')
        else:
            sprite = texture_manager.sprites.get(f'{state_prefix}_stand')
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        if sprite:
            if not self.facing_right:
                sprite = pygame.transform.flip(sprite, True, False)
            surface.blit(sprite, (screen_x, screen_y))
        else:
            # Fallback to colored rectangles
            if self.state == MARIO_STATE_SMALL:
                color = COLOR_MARIO_SMALL
            elif self.state == MARIO_STATE_SUPER:
                color = COLOR_MARIO_SUPER
            else:
                color = COLOR_MARIO_FIRE
            
            if self.invincible and (self.anim_timer // 2) % 4 < 2:
                color = (255, 255, 255)
            
            pygame.draw.rect(surface, color,
                            (screen_x, screen_y, self.width * SCALE, self.height * SCALE))

# ============================================================================
# ENTITY BASE CLASS
# ============================================================================

class Entity:
    """Base class for all entities"""
    
    def __init__(self, x, y, entity_type):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = 16
        self.height = 16
        self.type = entity_type
        self.dead = False
        self.on_ground = False
    
    def update(self, level, entities):
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > MAX_FALL_SPEED:
                self.vy = MAX_FALL_SPEED
        
        self.x += self.vx
        self.y += self.vy
        
        self.handle_level_collision(level)
        
        # FIXED: Mark entities as dead if they fall off the level
        if self.y > level.height * TILE_SIZE + 100:
            self.dead = True
    
    def handle_level_collision(self, level):
        self.on_ground = False
        
        left = int(self.x / TILE_SIZE)
        right = int((self.x + self.width) / TILE_SIZE)
        top = int(self.y / TILE_SIZE)
        bottom = int((self.y + self.height) / TILE_SIZE)
        
        if self.vy >= 0:
            for x in range(left, right + 1):
                if level.is_solid(x, bottom):
                    self.y = bottom * TILE_SIZE - self.height
                    self.vy = 0
                    self.on_ground = True
                    break
        
        elif self.vy < 0:
            for x in range(left, right + 1):
                if level.is_solid(x, top):
                    self.y = (top + 1) * TILE_SIZE
                    self.vy = 0
                    break
        
        left = int(self.x / TILE_SIZE)
        right = int((self.x + self.width) / TILE_SIZE)
        top = int(self.y / TILE_SIZE)
        bottom = int((self.y + self.height - 1) / TILE_SIZE)
        
        if self.vx > 0:
            for y in range(top, bottom + 1):
                if level.is_solid(right, y):
                    self.x = right * TILE_SIZE - self.width
                    self.vx = -self.vx
                    break
        
        elif self.vx < 0:
            for y in range(top, bottom + 1):
                if level.is_solid(left, y):
                    self.x = (left + 1) * TILE_SIZE
                    self.vx = -self.vx
                    break
    
    def draw(self, surface, camera_x):
        pass

# ============================================================================
# GOOMBA CLASS
# ============================================================================

class Goomba(Entity):
    """Goomba enemy"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ENTITY_GOOMBA)
        self.vx = -GOOMBA_SPEED
        self.width = 16
        self.height = 16
        self.stomped = False
        self.stomp_timer = 0
        self.anim_timer = 0
    
    def update(self, level, entities):
        if self.stomped:
            self.stomp_timer += 1
            if self.stomp_timer > 10:
                self.dead = True
            return
        
        self.anim_timer += 1
        super().update(level, entities)
        
        if self.on_ground:
            check_x = int((self.x + (self.width if self.vx > 0 else -1)) / TILE_SIZE)
            check_y = int((self.y + self.height + 1) / TILE_SIZE)
            if not level.is_solid(check_x, check_y):
                self.vx = -self.vx
    
    def stomp(self, game):
        """Goomba is stomped - FIXED: Added game parameter"""
        self.stomped = True
        self.height = 8
        self.stomp_timer = 0
    
    def draw(self, surface, camera_x):
        if self.dead:
            return
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        if self.stomped:
            sprite = texture_manager.sprites.get('goomba_stomped')
        else:
            walk_frame = (self.anim_timer // 10) % 2 + 1
            sprite = texture_manager.sprites.get(f'goomba_walk{walk_frame}')
        
        if sprite:
            surface.blit(sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, COLOR_GOOMBA,
                            (screen_x, screen_y, self.width * SCALE, self.height * SCALE))

# ============================================================================
# KOOPA CLASS
# ============================================================================

class Koopa(Entity):
    """Koopa Troopa enemy"""
    
    def __init__(self, x, y, is_red=False):
        entity_type = ENTITY_KOOPA_RED if is_red else ENTITY_KOOPA_GREEN
        super().__init__(x, y, entity_type)
        self.vx = -KOOPA_SPEED
        self.width = 16
        self.height = 24
        self.is_red = is_red
        self.anim_timer = 0
    
    def update(self, level, entities):
        self.anim_timer += 1
        super().update(level, entities)
        
        if self.is_red and self.on_ground:
            check_x = int((self.x + (self.width if self.vx > 0 else -1)) / TILE_SIZE)
            check_y = int((self.y + self.height + 1) / TILE_SIZE)
            if not level.is_solid(check_x, check_y):
                self.vx = -self.vx
    
    def stomp(self, game):
        """Koopa becomes shell - FIXED: Added game parameter"""
        self.dead = True
        game.entities.append(Shell(self.x, self.y + 8, self.is_red))
    
    def draw(self, surface, camera_x):
        if self.dead:
            return
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        walk_frame = (self.anim_timer // 10) % 2 + 1
        prefix = 'koopa_red' if self.is_red else 'koopa_green'
        sprite = texture_manager.sprites.get(f'{prefix}_walk{walk_frame}')
        
        if sprite:
            if self.vx > 0:
                sprite = pygame.transform.flip(sprite, True, False)
            surface.blit(sprite, (screen_x, screen_y))
        else:
            color = COLOR_KOOPA_RED if self.is_red else COLOR_KOOPA_GREEN
            pygame.draw.rect(surface, color,
                            (screen_x, screen_y, self.width * SCALE, self.height * SCALE))

# ============================================================================
# SHELL CLASS
# ============================================================================

class Shell(Entity):
    """Koopa shell"""
    
    def __init__(self, x, y, is_red=False):
        super().__init__(x, y, ENTITY_SHELL)
        self.vx = 0
        self.width = 16
        self.height = 16
        self.moving = False
        self.is_red = is_red
    
    def kick(self, right):
        self.moving = True
        self.vx = SHELL_KICK_SPEED if right else -SHELL_KICK_SPEED
    
    def update(self, level, entities):
        super().update(level, entities)
        
        if self.moving:
            shell_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            for entity in entities:
                if entity == self or entity.dead:
                    continue
                if entity.type in [ENTITY_GOOMBA, ENTITY_KOOPA_GREEN, ENTITY_KOOPA_RED]:
                    entity_rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
                    if shell_rect.colliderect(entity_rect):
                        entity.dead = True
    
    def stomp(self, game):
        """FIXED: Shell can be stomped - stops it"""
        if self.moving:
            self.vx = 0
            self.moving = False
    
    def draw(self, surface, camera_x):
        if self.dead:
            return
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        sprite_name = 'shell_red' if self.is_red else 'shell_green'
        sprite = texture_manager.sprites.get(sprite_name)
        
        if sprite:
            surface.blit(sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, COLOR_SHELL,
                            (screen_x, screen_y, self.width * SCALE, self.height * SCALE))

# ============================================================================
# MUSHROOM CLASS
# ============================================================================

class Mushroom(Entity):
    """Super Mushroom power-up"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ENTITY_MUSHROOM)
        self.vx = MUSHROOM_SPEED
        self.width = 16
        self.height = 16
        self.spawning = True
        self.spawn_timer = 20
    
    def update(self, level, entities):
        if self.spawning:
            self.spawn_timer -= 1
            self.y -= 0.5
            if self.spawn_timer <= 0:
                self.spawning = False
            return
        
        super().update(level, entities)
    
    def collect(self, mario):
        mario.power_up_mushroom()
    
    def draw(self, surface, camera_x):
        if self.dead:
            return
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        sprite = texture_manager.sprites.get('mushroom')
        
        if sprite:
            surface.blit(sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, COLOR_MUSHROOM,
                            (screen_x, screen_y, self.width * SCALE, self.height * SCALE))

# ============================================================================
# FIRE FLOWER CLASS
# ============================================================================

class FireFlower(Entity):
    """Fire Flower power-up"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ENTITY_FIRE_FLOWER)
        self.width = 16
        self.height = 16
        self.spawning = True
        self.spawn_timer = 20
    
    def update(self, level, entities):
        if self.spawning:
            self.spawn_timer -= 1
            self.y -= 0.5
            if self.spawn_timer <= 0:
                self.spawning = False
            return
    
    def collect(self, mario):
        mario.power_up_fire_flower()
    
    def draw(self, surface, camera_x):
        if self.dead:
            return
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        sprite = texture_manager.sprites.get('fire_flower')
        
        if sprite:
            surface.blit(sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, COLOR_FIRE_FLOWER,
                            (screen_x, screen_y, self.width * SCALE, self.height * SCALE))

# ============================================================================
# STAR CLASS
# ============================================================================

class Star(Entity):
    """Star power-up"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ENTITY_STAR)
        self.vx = MUSHROOM_SPEED
        self.width = 16
        self.height = 16
        self.spawning = True
        self.spawn_timer = 20
        self.bounce_timer = 0
    
    def update(self, level, entities):
        if self.spawning:
            self.spawn_timer -= 1
            self.y -= 0.5
            if self.spawn_timer <= 0:
                self.spawning = False
            return
        
        self.bounce_timer += 1
        if self.on_ground and self.bounce_timer > 10:
            self.vy = MUSHROOM_BOUNCE_VELOCITY
            self.bounce_timer = 0
        
        super().update(level, entities)
    
    def collect(self, mario):
        mario.power_up_star()
    
    def draw(self, surface, camera_x):
        if self.dead:
            return
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        sprite = texture_manager.sprites.get('star')
        
        if sprite:
            surface.blit(sprite, (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, COLOR_STAR,
                            (screen_x, screen_y, self.width * SCALE, self.height * SCALE))

# ============================================================================
# FIREBALL CLASS
# ============================================================================

class Fireball(Entity):
    """Mario's fireball projectile - FIXED: Bouncing and off-screen behavior"""
    
    def __init__(self, x, y, moving_right):
        super().__init__(x, y, ENTITY_FIREBALL)
        self.vx = 4 if moving_right else -4
        self.vy = 0
        self.width = 8
        self.height = 8
        self.lifetime = 180
        self.bounce_count = 0
        self.anim_timer = 0
    
    def update(self, level, entities):
        """Update fireball - FIXED: Proper bouncing"""
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.dead = True
            return
        
        self.anim_timer += 1
        
        # FIXED: Fireball bounces instead of exploding
        old_on_ground = self.on_ground
        super().update(level, entities)
        
        # Bounce when hitting ground
        if self.on_ground and not old_on_ground:
            self.vy = -4.0  # FIXED: Bounces with consistent height
            self.bounce_count += 1
        
        # Check collision with enemies
        fireball_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for entity in entities:
            if entity == self or entity.dead:
                continue
            if entity.type in [ENTITY_GOOMBA, ENTITY_KOOPA_GREEN, ENTITY_KOOPA_RED, ENTITY_SHELL]:
                entity_rect = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
                if fireball_rect.colliderect(entity_rect):
                    entity.dead = True
                    self.dead = True
                    break
    
    def draw(self, surface, camera_x):
        if self.dead:
            return
        
        screen_x = (self.x - camera_x) * SCALE
        screen_y = self.y * SCALE
        
        sprite = texture_manager.sprites.get('fireball')
        
        if sprite:
            surface.blit(sprite, (screen_x, screen_y))
        else:
            pygame.draw.circle(surface, COLOR_FIREBALL,
                              (int(screen_x + self.width * SCALE / 2),
                               int(screen_y + self.height * SCALE / 2)),
                              int(self.width * SCALE / 2))

# ============================================================================
# GAME CLASS
# ============================================================================

class Game:
    """Main game state and loop"""
    
    def __init__(self):
        self.preview_sheet_index = 0
        self.reset()
    
    def reset(self):
        self.level = self.create_test_level()
        self.mario = Mario(32, 32)
        self.entities = []
        self.spawn_test_entities()
        self.running = True
        self.current_level = 1
        self.level_complete = False
    
    def create_test_level(self):
        level_width = 200
        level_height = 15
        level_data = [[TILE_EMPTY for _ in range(level_width)] for _ in range(level_height)]
        
        for x in range(level_width):
            level_data[13][x] = TILE_GROUND
            level_data[14][x] = TILE_GROUND
        
        for x in range(5, 15):
            for y in range(11, 13):
                level_data[y][x] = TILE_GROUND
        
        for x in [20, 22, 24]:
            level_data[9][x] = TILE_QUESTION
        
        for x in range(30, 36):
            level_data[9][x] = TILE_BRICK
        
        for x in range(40, 45):
            level_data[10][x] = TILE_GROUND
        
        level_data[11][50] = TILE_PIPE_UL
        level_data[11][51] = TILE_PIPE_UR
        level_data[12][50] = TILE_PIPE_ML
        level_data[12][51] = TILE_PIPE_MR
        
        for i in range(5):
            for j in range(i + 1):
                level_data[12 - j][60 + i] = TILE_GROUND
        
        for x in range(80, 90):
            level_data[8][x] = TILE_GROUND
        
        for y in range(5, 13):
            level_data[y][190] = TILE_FLAGPOLE
        
        for x in range(185, 195):
            level_data[12][x] = TILE_GROUND
        
        return Level(level_data)
    
    def spawn_test_entities(self):
        self.entities.append(Goomba(300, 180))
        self.entities.append(Goomba(400, 180))
        self.entities.append(Goomba(500, 180))
        self.entities.append(Koopa(600, 180, is_red=False))
        self.entities.append(Koopa(700, 180, is_red=True))
        self.entities.append(Koopa(800, 180, is_red=False))
    
    def update(self, keys):
        mario_tile_x = int((self.mario.x + self.mario.width / 2) / TILE_SIZE)
        if self.level.get_tile(mario_tile_x, 5) == TILE_FLAGPOLE:
            self.level_complete = True
        
        self.mario.update(keys, self.level, self.entities)
        self.level.update(self.mario)
        
        # FIXED: Remove entities that are far off-screen to prevent regeneration
        visible_left = self.level.camera_x - TILE_SIZE * 2
        visible_right = self.level.camera_x + NES_WIDTH + TILE_SIZE * 2
        
        for entity in self.entities[:]:
            if entity.dead:
                self.entities.remove(entity)
            # FIXED: Don't remove fireballs that go off-screen, they expire naturally
            elif entity.type != ENTITY_FIREBALL and (entity.x < visible_left - 100 or entity.x > visible_right + 100):
                # Only remove if way off screen
                pass
            else:
                entity.update(self.level, self.entities)
        
        if self.mario.dead and self.mario.death_timer > DEATH_ANIMATION_TIME:
            if self.mario.lives > 0:
                self.mario = Mario(32, 32)
            else:
                self.running = False
        
        if self.level_complete:
            self.current_level += 1
            self.reset()
    
    def draw(self):
        screen.fill(COLOR_SKY)

        if SHOW_SPRITE_SHEET and texture_manager.use_textures:
            self.draw_sprite_sheet_preview()
            return

        self.level.draw(screen)

        for entity in self.entities:
            entity.draw(screen, self.level.camera_x)

        self.mario.draw(screen, self.level.camera_x)
        self.draw_hud()

        if DEBUG_INFO:
            self.draw_debug_info()

        if SHOW_SPRITE_LABELS:
            self.draw_sprite_labels()
    
    def draw_sprite_sheet_preview(self):
        """Draw sprite sheet with grid overlay — F3 cycles sheets, F2 exits"""
        if len(texture_manager.sprite_sheets) == 0:
            return

        sheet_names = [
            "Sheet 0: 50365.png (Mario)",
            "Sheet 1: 52570.png (Tiles)",
            "Sheet 2: 52572.png (Enemies)",
            "Sheet 3: 52574.png (Power-ups)",
        ]

        idx = self.preview_sheet_index % len(texture_manager.sprite_sheets)
        sheet = texture_manager.sprite_sheets[idx]
        sheet_width, sheet_height = sheet.get_size()

        # Scale sheet to fit screen if needed
        sw = NES_WIDTH * SCALE
        sh = NES_HEIGHT * SCALE
        scaled = pygame.transform.scale(sheet, (min(sheet_width, sw), min(sheet_height, sh - 60)))
        screen.blit(scaled, (0, 0))

        # Grid overlay — 17px apart (16px sprite + 1px border)
        for x in range(0, min(sheet_width, sw), 17):
            pygame.draw.line(screen, (255, 0, 0), (x, 0), (x, min(sheet_height, sh - 60)), 1)
        for y in range(0, min(sheet_height, sh - 60), 17):
            pygame.draw.line(screen, (255, 0, 0), (0, y), (min(sheet_width, sw), y), 1)

        # Grid col,row labels
        small_font = pygame.font.Font(None, 12)
        for gy in range(0, min(sheet_height, sh - 60) // 17):
            for gx in range(0, min(sheet_width, sw) // 17):
                label = small_font.render(f"{gx},{gy}", True, (255, 255, 0))
                screen.blit(label, (gx * 17 + 1, gy * 17 + 1))

        # Info bar at bottom
        sheet_label = sheet_names[idx] if idx < len(sheet_names) else f"Sheet {idx}"
        pygame.draw.rect(screen, (0, 0, 0), (0, sh - 58, sw, 58))
        lines = [
            f"{sheet_label}  ({sheet_width}x{sheet_height}px)",
            "F2=exit  F3=next sheet  |  Coords shown as col,row",
            "get_sprite_grid(sheet_index, col, row, width, height)",
        ]
        for i, line in enumerate(lines):
            t = font.render(line, True, (255, 255, 255))
            screen.blit(t, (4, sh - 56 + i * 18))

    def draw_sprite_labels(self):
        """F4 debug: draw sprite key names on every game object"""
        small_font = pygame.font.Font(None, 12)

        def label(text, x, y):
            surf = small_font.render(text, True, (255, 255, 0))
            pygame.draw.rect(screen, (0, 0, 0),
                             (x - 1, y - 1, surf.get_width() + 2, surf.get_height() + 2))
            screen.blit(surf, (x, y))

        cam = self.level.camera_x
        sx = (self.mario.x - cam) * SCALE
        sy = self.mario.y * SCALE
        state_prefix = ['mario_small', 'mario_super', 'mario_fire'][self.mario.state]
        label(f"{state_prefix}_stand", int(sx), int(sy))

        for entity in self.entities:
            ex = (entity.x - cam) * SCALE
            ey = entity.y * SCALE
            etype = {1: 'goomba_walk1', 2: 'koopa_green_walk1',
                     3: 'koopa_red_walk1', 4: 'mushroom',
                     5: 'fire_flower', 6: 'star', 7: 'shell_green',
                     8: 'fireball'}.get(entity.type, '?')
            label(etype, int(ex), int(ey))

        # Tile labels for visible tiles
        start_x = int(self.level.camera_x / TILE_SIZE)
        end_x = start_x + (NES_WIDTH // TILE_SIZE) + 2
        tile_names = {1: 'ground', 2: 'brick', 3: 'question',
                      4: 'q_used', 5: 'pipe_ul', 6: 'pipe_ur',
                      7: 'pipe_ml', 8: 'pipe_mr'}
        for y in range(self.level.height):
            for x in range(start_x, min(end_x, self.level.width)):
                tile = self.level.get_tile(x, y)
                if tile in tile_names:
                    tx = (x * TILE_SIZE - self.level.camera_x) * SCALE
                    ty = y * TILE_SIZE * SCALE
                    label(tile_names[tile], int(tx), int(ty))
    
    def draw_hud(self):
        pygame.draw.rect(screen, (0, 0, 0), (0, 0, NES_WIDTH * SCALE, 16 * SCALE))
        
        text = font.render(f"LIVES: {self.mario.lives}", True, (255, 255, 255))
        screen.blit(text, (10, 5))
        
        text = font.render(f"WORLD 1-{self.current_level}", True, (255, 255, 255))
        screen.blit(text, (200 * SCALE, 5))
        
        state_text = ["SMALL", "SUPER", "FIRE"][self.mario.state]
        text = font.render(f"STATE: {state_text}", True, (255, 255, 255))
        screen.blit(text, (350 * SCALE, 5))
        
        # Show fireball count for debugging
        if self.mario.state == MARIO_STATE_FIRE:
            fb_count = sum(1 for e in self.entities if e.type == ENTITY_FIREBALL and not e.dead)
            text = font.render(f"FB: {fb_count}/2", True, (255, 255, 255))
            screen.blit(text, (450 * SCALE, 5))
    
    def draw_debug_info(self):
        debug_texts = [
            f"FPS: {int(clock.get_fps())}",
            f"Mario Pos: ({int(self.mario.x)}, {int(self.mario.y)})",
            f"Mario Vel: ({self.mario.vx:.2f}, {self.mario.vy:.2f})",
            f"On Ground: {self.mario.on_ground}",
            f"Entities: {len(self.entities)}",
            f"Camera X: {int(self.level.camera_x)}",
            f"Invincible: {self.mario.invincible} ({self.mario.invincibility_timer})",
        ]
        
        y_offset = 20 * SCALE
        for text_str in debug_texts:
            text = font.render(text_str, True, (255, 255, 255))
            screen.blit(text, (10, y_offset))
            y_offset += 20

# ============================================================================
# MAIN GAME LOOP
# ============================================================================

try:
    game = Game()
    keys_pressed = pygame.key.get_pressed()

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z or event.key == pygame.K_s:
                    game.mario.shoot_fireball(game.entities)
                if event.key == pygame.K_r:
                    game.reset()
                if event.key == pygame.K_F1:
                    DEBUG_INFO = not DEBUG_INFO
                if event.key == pygame.K_F2:
                    SHOW_SPRITE_SHEET = not SHOW_SPRITE_SHEET
                if event.key == pygame.K_F3:
                    game.preview_sheet_index = (game.preview_sheet_index + 1) % max(1, len(texture_manager.sprite_sheets))
                    SHOW_SPRITE_SHEET = True  # auto-open viewer when cycling
                if event.key == pygame.K_F4:
                    SHOW_SPRITE_LABELS = not SHOW_SPRITE_LABELS
                if event.key == pygame.K_g:
                    SHOW_GRID = not SHOW_GRID
                if event.key == pygame.K_1:
                    game.mario.state = MARIO_STATE_SMALL
                if event.key == pygame.K_2:
                    game.mario.state = MARIO_STATE_SUPER
                if event.key == pygame.K_3:
                    game.mario.state = MARIO_STATE_FIRE
                if event.key == pygame.K_4:
                    game.mario.power_up_star()

        keys_pressed = pygame.key.get_pressed()
        game.update(keys_pressed)
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

except Exception as e:
    traceback.print_exc()

finally:
    sys.stderr.flush()
    sys.stdout.flush()
    pygame.quit()
    sys.exit()
