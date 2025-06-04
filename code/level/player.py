# Di player.py

import pygame
from settings import * # Pastikan TILESIZE diimpor dari sini

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites, camera_input=None):
        super().__init__(groups)
        try:
            self.image = pygame.image.load('graphics/player/down_idle/idle_down.png').convert_alpha()
        except pygame.error as e:
            print(f"Error loading player image: {e}. Creating placeholder.")
            self.image = pygame.Surface((TILESIZE, TILESIZE))
            self.image.fill((0, 0, 255)) # Placeholder biru
            
        # Initialize rect with its center at the provided 'pos'
        self.rect = self.image.get_rect(center=pos) 
        
        # Initialize hitbox relative to the rect; inflate keeps the center
        self.hitbox = self.rect.inflate(0, -10) 
        # Ensure hitbox is perfectly centered with the rect after inflation
        # (though inflate(0, even_number) should preserve the center)
        self.hitbox.center = self.rect.center

        # Tile-based Movement
        self.tile_size = TILESIZE
        self.move_cooldown_duration = 200  # Cooldown dalam milidetik antar gerakan
        self.last_move_time = 0

        self.obstacle_sprites = obstacle_sprites
        self.inventory = {'heart': 0}

        # Kamera & Gestur (jika digunakan)
        self.game_camera = camera_input
        self.predicted_label = 0 
        self.control_with_gesture = True 
        self.g_key_was_pressed = False # Untuk toggle kontrol gestur

        # Status (untuk animasi, dll. - disederhanakan)
        self.status = 'down_idle' # Status awal
        # Atribut animasi (jika Anda memilikinya)
        # self.animations = {'up': [], 'down': [], ...} 
        # self.frame_index = 0
        # self.animation_speed = 0.15


    def input(self):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        can_move_now = (current_time - self.last_move_time > self.move_cooldown_duration)
        
        attempted_move_dx_tile = 0
        attempted_move_dy_tile = 0
        keyboard_input_made = False

        if can_move_now:
            # Kontrol Keyboard
            # commented out to avoid confusion with gesture control (debugging purposes)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                attempted_move_dy_tile = -1
                self.status = 'up' 
                keyboard_input_made = True
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                attempted_move_dy_tile = 1
                self.status = 'down'
                keyboard_input_made = True
            
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if attempted_move_dy_tile == 0: # Prefer vertical movement if both pressed
                    attempted_move_dx_tile = -1
                    self.status = 'left'
                    keyboard_input_made = True
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if attempted_move_dy_tile == 0: # Prefer vertical movement if both pressed
                    attempted_move_dx_tile = 1
                    self.status = 'right'
                    keyboard_input_made = True

            # Kontrol Gestur
            if not keyboard_input_made and self.control_with_gesture and self.game_camera:
                if self.predicted_label == 0 : # Atas
                    attempted_move_dy_tile = -1
                    self.status = 'up'
                elif self.predicted_label == 2: # Bawah
                    attempted_move_dy_tile = 1
                    self.status = 'down'
                # Tambahkan gestur untuk kiri/kanan jika diperlukan
                elif self.predicted_label == 3 and attempted_move_dy_tile == 0: # Kiri
                    attempted_move_dx_tile = -1
                    self.status = 'left'
                elif self.predicted_label == 4 and attempted_move_dy_tile == 0: # Kanan
                    attempted_move_dx_tile = 1
                    self.status = 'right'
            
            if attempted_move_dx_tile != 0 or attempted_move_dy_tile != 0:
                # Calculate target center position
                target_center_x = self.rect.centerx + attempted_move_dx_tile * self.tile_size
                target_center_y = self.rect.centery + attempted_move_dy_tile * self.tile_size

                # Create a temporary hitbox at the target center for collision checking
                future_hitbox = self.hitbox.copy()
                future_hitbox.center = (target_center_x, target_center_y)

                if not self.check_obstacle_collision(future_hitbox):
                    # Move player if no collision
                    self.rect.center = (target_center_x, target_center_y)
                    self.hitbox.center = self.rect.center # Keep hitbox centered with rect
                    self.last_move_time = current_time
                else:
                    # Optionally, reset status to idle if move failed
                    # if 'idle' in self.status: # e.g. 'up_idle', 'down_idle'
                    #    pass # Or set a generic idle
                    # else:
                    #    self.status = self.status.split('_')[0] + '_idle' if '_' not in self.status else self.status # Basic idle logic
                    pass # For now, status remains as the attempted move direction

        # Toggle gesture control
        if keys[pygame.K_g]:
            if not self.g_key_was_pressed:
                self.control_with_gesture = not self.control_with_gesture
                print(f"Gesture control: {'Enabled' if self.control_with_gesture else 'Disabled'}")
            self.g_key_was_pressed = True
        else:
            self.g_key_was_pressed = False

    def check_obstacle_collision(self, future_hitbox):
        for sprite in self.obstacle_sprites:
            if hasattr(sprite, 'hitbox') and sprite.hitbox.colliderect(future_hitbox):
                return True 
        return False 

    def set_predicted_gesture_label(self, label):
        self.predicted_label = label

    def collect_item(self, item_name):
        if item_name in self.inventory:
            self.inventory[item_name] += 1
        else:
            self.inventory[item_name] = 1
        print(f"Player collected {item_name}. Inventory: {self.inventory}")

    def animate(self):
        # Ganti dengan logika animasi Anda yang sebenarnya
        # Misalnya, jika Anda memiliki self.animations, self.status, self.frame_index, self.animation_speed:
        # current_animation_frames = self.animations.get(self.status, self.animations.get('down_idle')) # Fallback to default
        # self.frame_index += self.animation_speed
        # if self.frame_index >= len(current_animation_frames):
        #     self.frame_index = 0
        # self.image = current_animation_frames[int(self.frame_index)]
        # self.rect = self.image.get_rect(center=self.hitbox.center) # Update visual rect around hitbox
        pass


    def update(self):
        self.input()
        self.animate() 
        # Hitbox is the source of truth for position; rect is for visuals.
        # Ensure animate() updates self.rect based on self.hitbox.center if image changes.
