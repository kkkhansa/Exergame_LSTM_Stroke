# Di player.py

import pygame
from settings import * 

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, camera_input=None):
        super().__init__(groups)
        try:
            self.image = pygame.image.load('graphics/player/down_idle/idle_down.png').convert_alpha()
        except pygame.error as e:
            print(f"Error loading player image: {e}. Creating placeholder.")
            self.image = pygame.Surface((TILESIZE, TILESIZE))
            self.image.fill((0, 0, 255)) # Blue placeholder
            
        self.rect = self.image.get_rect(center=pos) 
        self.hitbox = self.rect.inflate(0, -10) 
        self.hitbox.center = self.rect.center

        # Tile-based Movement
        self.tile_size = TILESIZE
        self.move_cooldown_duration = 200  # Cooldown for keyboard movement
        self.last_move_time = 0

        self.obstacle_sprites = obstacle_sprites
        self.inventory = {'heart': 0}

        # Gesture Control Toggle
        self.control_with_gesture = True 
        self.g_key_was_pressed = False

        # Status
        self.status = 'down_idle'

    def input(self):
        """Handles keyboard input and toggling gesture control."""
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        # --- Keyboard Movement (respects cooldown) ---
        can_move_now = (current_time - self.last_move_time > self.move_cooldown_duration)
        if can_move_now:
            move_dx_tile = 0
            move_dy_tile = 0
            
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                move_dy_tile = -1
                self.status = 'up'
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                move_dy_tile = 1
                self.status = 'down'
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if move_dy_tile == 0:
                    move_dx_tile = -1
                    self.status = 'left'
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if move_dy_tile == 0:
                    move_dx_tile = 1
                    self.status = 'right'

            if move_dx_tile != 0 or move_dy_tile != 0:
                self.move_tile(move_dx_tile, move_dy_tile)
                self.last_move_time = current_time # Apply cooldown only after a keyboard move

        # --- Toggle Gesture Control ---
        if keys[pygame.K_g] and not self.g_key_was_pressed:
            self.control_with_gesture = not self.control_with_gesture
            print(f"Gesture control: {'Enabled' if self.control_with_gesture else 'Disabled'}")
        self.g_key_was_pressed = keys[pygame.K_g]


    def execute_gesture_move(self, action_label):
        """
        Executes a move based on a confirmed gesture action.
        This bypasses the standard move cooldown, as the dwell time is the cooldown.
        """
        if not self.control_with_gesture:
            return

        move_dx_tile, move_dy_tile = 0, 0
        if action_label == 0: # Up
            move_dy_tile = -1; self.status = 'up'
        elif action_label == 1: # Down
            move_dy_tile = 1; self.status = 'down'
        elif action_label == 2: # Right
            move_dx_tile = 1; self.status = 'right'
        elif action_label == 3: # Left
            move_dx_tile = -1; self.status = 'left'

        if move_dx_tile != 0 or move_dy_tile != 0:
            self.move_tile(move_dx_tile, move_dy_tile)

    def move_tile(self, dx_tile, dy_tile):
        """Moves the player by a number of tiles, checking for collisions first."""
        target_center_x = self.rect.centerx + dx_tile * self.tile_size
        target_center_y = self.rect.centery + dy_tile * self.tile_size

        future_hitbox = self.hitbox.copy()
        future_hitbox.center = (target_center_x, target_center_y)

        if not self.check_obstacle_collision(future_hitbox):
            self.rect.center = (target_center_x, target_center_y)
            self.hitbox.center = self.rect.center
        else:
            # Optionally, revert status to idle if move failed
            pass

    def check_obstacle_collision(self, future_hitbox):
        for sprite in self.obstacle_sprites:
            if hasattr(sprite, 'hitbox') and sprite.hitbox.colliderect(future_hitbox):
                return True 
        return False 

    def collect_item(self, item_name):
        self.inventory.setdefault(item_name, 0)
        self.inventory[item_name] += 1
        print(f"Player collected {item_name}. Inventory: {self.inventory}")

    def animate(self):
        # Placeholder for animation logic
        pass

    def update(self, **kwargs):
        # The gesture_action is passed from TrialLevel to player.execute_gesture_move
        # The keyboard input is handled by self.input()
        self.input()
        self.animate()
