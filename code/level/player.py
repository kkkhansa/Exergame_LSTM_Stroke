# Di player.py

import pygame
from settings import * # Asumsikan settings.py punya SPEED, dll.
# from entity import Entity # Jika Anda menggunakan kelas Entity dasar

class Player(pygame.sprite.Sprite): # Atau class Player(Entity):
    def __init__(self, pos, groups, obstacle_sprites, camera_input=None): # Contoh argumen
        super().__init__(groups)
        self.image = pygame.image.load('graphics/player/down_idle/idle_down.png').convert_alpha() # Contoh gambar
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -10) # Contoh hitbox

        # Movement
        self.direction = pygame.math.Vector2()
        self.speed = 5 # Dari settings.py

        self.obstacle_sprites = obstacle_sprites
        self.inventory = {'heart': 0} # Inisialisasi inventaris di sini

        # Kamera & Gestur (jika digunakan)
        self.game_camera = camera_input
        self.predicted_label = 0 # Untuk gestur
        self.control_with_gesture = True # Flag untuk beralih mode kontrol

        # Status (untuk animasi, dll. - disederhanakan)
        self.status = 'down_idle'
        self.frame_index = 0
        self.animation_speed = 0.15


    def input(self):
        keys = pygame.key.get_pressed()

        # Reset arah setiap frame
        self.direction.x = 0
        self.direction.y = 0

        # Kontrol Keyboard (prioritaskan ini jika tombol ditekan)
        keyboard_input_active = False
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction.y = -1
            self.status = 'up'
            keyboard_input_active = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction.y = 1
            self.status = 'down'
            keyboard_input_active = True
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
            self.status = 'left'
            keyboard_input_active = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
            self.status = 'right'
            keyboard_input_active = True

        # Jika tidak ada input keyboard dan kontrol gestur aktif
        if not keyboard_input_active and self.control_with_gesture and self.game_camera:
            # Logika gestur menggunakan self.predicted_label
            # (Kode ini sebelumnya ada di Player.input() di versi awal Anda)
            if self.predicted_label == 1: # Asumsi 1 = atas
                self.direction.y = -1
                self.status = 'up'
            elif self.predicted_label == 2: # Asumsi 2 = bawah
                self.direction.y = 1
                self.status = 'down'
            # ... tambahkan untuk kiri dan kanan jika ada labelnya
            # else:
                # Jika tidak ada gestur yang cocok, arah tetap (0,0) dari keyboard
                # atau Anda bisa set status ke idle berdasarkan arah terakhir dari keyboard/gestur

        # Toggle mode kontrol gestur (contoh dengan tombol G)
        if keys[pygame.K_g] and not self.g_key_pressed: # Mencegah toggle berulang jika tombol ditahan
            self.control_with_gesture = not self.control_with_gesture
            print(f"Gesture control: {'Enabled' if self.control_with_gesture else 'Disabled'}")
        self.g_key_pressed = keys[pygame.K_g] # Simpan status tombol G


    def set_predicted_gesture_label(self, label):
        self.predicted_label = label

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()

        self.hitbox.x += self.direction.x * speed
        self.collision('horizontal')
        self.hitbox.y += self.direction.y * speed
        self.collision('vertical')
        self.rect.center = self.hitbox.center
    
    def collision(self,direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.x > 0: # Pindah ke kanan
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0: # Pindah ke kiri
                        self.hitbox.left = sprite.hitbox.right

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.y > 0: # Pindah ke bawah
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0: # Pindah ke atas
                        self.hitbox.top = sprite.hitbox.bottom
    
    def collect_item(self, item_name):
        if item_name in self.inventory:
            self.inventory[item_name] += 1
        else:
            self.inventory[item_name] = 1
        print(f"Player collected {item_name}. Inventory: {self.inventory}")

    # Anda mungkin perlu menambahkan metode get_status dan animate jika belum ada/disederhanakan
    # def get_status(self): ...
    # def animate(self): ...

    def update(self):
        self.input() # Panggil input untuk mendapatkan arah
        # self.get_status() # Update status berdasarkan arah dan aksi
        # self.animate() # Update animasi
        self.move(self.speed) # Pindahkan pemain