import pygame
from settings import *
from tile import Tile
from level.player import Player # Pastikan player.py bisa menangani input keyboard DAN/ATAU gestur
from level.support import * # Pastikan path ini benar jika level1.py ada di dalam folder 'level'
from random import choice
from ui import UI
# from camera import HandGestureCamera # Tidak perlu diimpor di sini jika sudah dioper dari main.py

# Kelas Item Sederhana
class Item(pygame.sprite.Sprite):
    def __init__(self, pos, groups, item_type, surface=None):
        super().__init__(groups)
        self.sprite_type = 'item'
        self.item_type = item_type
        
        if surface:
            self.image = surface
        else:
            self.image = pygame.Surface((TILESIZE, TILESIZE)) # Ukuran default
            if self.item_type == 'heart':
               # Pastikan path ini benar relatif terhadap direktori kerja saat game dijalankan
               try:
                loaded_image = pygame.image.load('graphics/items/heart.png').convert_alpha()
                   # Skala ulang gambar agar sesuai dengan TILESIZE x TILESIZE
                self.image = pygame.transform.scale(loaded_image, (TILESIZE, TILESIZE)) # Tambahkan/Ubah baris ini
                
               except pygame.error as e:
                   print(f"Error loading heart item image: {e}. Using placeholder.")
                   self.image.fill('red') # Placeholder jika gagal load
            else:
                self.image.fill('grey')
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(0, 0)


class Level:
    def __init__(self, camera_instance): # Menerima instance kamera dari main.py
        self.display_surface = pygame.display.get_surface()
        self.game_paused = False

        self.visible_sprites = YSortCameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()

        self.game_camera = camera_instance # Simpan instance kamera

        # sprite setup
        # self.player akan dibuat di create_map()
        self.player = None 
        self.create_map() # Ini akan menginisialisasi self.player

        # user interface
        self.ui = UI()
        if self.game_camera: # Pastikan kamera ada sebelum di-set ke UI
            self.ui.set_camera(self.game_camera) # Oper instance kamera ke UI

        # Inisialisasi player.inventory (lebih baik di Player class __init__)
        # Pemeriksaan ini dilakukan setelah self.player dibuat di create_map
        if self.player: # Pastikan player sudah ada setelah create_map
            if not hasattr(self.player, 'inventory') or not isinstance(self.player.inventory, dict):
                self.player.inventory = {'heart': 0}
            elif 'heart' not in self.player.inventory:
                self.player.inventory['heart'] = 0
        else:
            print("LEVEL WARNING: Player object not created after create_map(). UI might not function correctly.")


    def create_map(self):
        layouts = {
            'boundary': import_csv_layout("map/map_FloorBlocks.csv"),
            'grass': import_csv_layout("map/map_Grass.csv"),
            'object': import_csv_layout("map/map_Objects.csv"),
            'entities': import_csv_layout("map/map_Entities.csv")
        }
        graphics = {
            'grass': import_folder("graphics/grass"),
            'objects': import_folder("graphics/objects"),
            'heart': pygame.image.load("graphics/items/heart.png").convert_alpha()
        }

        for style,layout in layouts.items():
            for row_index,row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILESIZE
                        y = row_index * TILESIZE
                        if style == 'boundary':
                            Tile((x,y),[self.obstacle_sprites],'invisible')
                        if style == 'grass':
                            random_grass_image = choice(graphics['grass'])
                            Tile((x,y), [self.visible_sprites,self.obstacle_sprites], 'grass', random_grass_image)
                        if style == 'object':
                            surf = graphics['objects'][int(col)]
                            Tile((x,y),[self.visible_sprites,self.obstacle_sprites],'object',surf)
                        if style == 'entities':
                            if col == '394': # ID Pemain
                                initial_predicted_label = 0 # Default jika kamera tidak ada atau tidak dipakai awal
                                if self.game_camera:
                                     # Anda mungkin ingin memanggil process sekali untuk mendapatkan label awal
                                     # atau biarkan Player yang mengambilnya di update pertamanya.
                                     # Untuk sekarang, kita bisa asumsikan Player akan menangani ini.
                                     # initial_predicted_label = self.game_camera.get_predicted_label() # Jika metode ini ada di camera.py
                                     pass


                                self.player = Player(
                                    pos=(x + TILESIZE // 2, y + TILESIZE // 2),
                                    groups=[self.visible_sprites],
                                    obstacle_sprites=self.obstacle_sprites,
                                    # Argumen untuk gestur kamera dan input keyboard akan ditangani di Player
                                    # Jika Player butuh instance kamera:
                                    # camera_input=self.game_camera 
                                )
                                # Pastikan Player.__init__ diperbarui untuk menerima argumen baru jika ada
                                # (misalnya, untuk kontrol keyboard atau referensi kamera)

                                # Inisialisasi inventaris di sini setelah player dibuat, jika belum di Player.__init__
                                if not hasattr(self.player, 'inventory') or not isinstance(self.player.inventory, dict):
                                    self.player.inventory = {'heart': 0}
                                elif 'heart' not in self.player.inventory:
                                     self.player.inventory['heart'] = 0

                            elif col in ['390', '391', '392', '393']: # ID Item 'heart'
                                Item(
                                    (x + TILESIZE // 2, y + TILESIZE // 2),
                                    [self.visible_sprites, self.item_sprites],
                                    'heart',
                                    graphics['heart']
                                )
    
    def player_item_collection_logic(self):
        if self.player:
            collided_items = pygame.sprite.spritecollide(self.player, self.item_sprites, True) # True untuk dokill
            for item_sprite in collided_items:
                if item_sprite.item_type == 'heart':
                    # Panggil metode di player untuk menambah item (praktik terbaik)
                    if hasattr(self.player, 'collect_item'):
                        self.player.collect_item('heart')
                    else: # Fallback jika metode collect_item tidak ada di Player
                        if 'heart' in self.player.inventory:
                            self.player.inventory['heart'] += 1
                        else:
                            self.player.inventory['heart'] = 1
                    print(f"Collected heart! Total: {self.player.inventory.get('heart', 0)}")

    def toggle_menu(self):
        self.game_paused = not self.game_paused

    def run(self):
        # Proses input kamera untuk gestur (jika digunakan)
        if self.game_camera and self.player and hasattr(self.player, 'control_with_gesture'): 
            # Asumsikan Player memiliki atribut/metode untuk menandakan kontrol gestur
            if self.player.control_with_gesture: # Contoh flag di Player
                self.game_camera.process() # Update prediksi gestur
                predicted_label = self.game_camera.get_predicted_label() # Dapatkan label terbaru
                if hasattr(self.player, 'set_predicted_gesture_label'):
                    self.player.set_predicted_gesture_label(predicted_label) # Oper ke player
                else: # Cara lama jika player masih menggunakan predicted_label secara langsung
                    self.player.predicted_label = predicted_label


        # Pemain akan menangani input keyboard di dalam metode update()-nya sendiri
        # yang dipanggil oleh self.visible_sprites.update()

        self.visible_sprites.custom_draw(self.player)
        
        if hasattr(self, 'ui') and self.player:
            self.ui.display(self.player)

        if self.game_paused:
            # Logika menu pause
            pass
        else:
            # Update game logic
            self.visible_sprites.update() # Ini akan memanggil Player.update()
            if self.player:
                self.player_item_collection_logic()


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

        try:
            self.floor_surf = pygame.image.load("graphics/tilemap/Background.png").convert()
        except pygame.error as e:
            print(f"Error loading background image for YSortCameraGroup: {e}. Creating fallback.")
            self.floor_surf = pygame.Surface((self.display_surface.get_width(), self.display_surface.get_height()))
            self.floor_surf.fill((30,30,30)) # Warna fallback abu-abu gelap
        self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

    def custom_draw(self,player):
        if player:
            self.offset.x = player.rect.centerx - self.half_width
            self.offset.y = player.rect.centery - self.half_height
        else:
            self.offset.x = 0
            self.offset.y = 0

        floor_offset_pos = self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf,floor_offset_pos)

        for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image,offset_pos)