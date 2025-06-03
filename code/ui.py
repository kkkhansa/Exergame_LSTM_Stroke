import pygame
from settings import *

from camera import HandGestureCamera

class UI:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 30)
        
        # Load item graphics (create default if not found)
        self.item_graphics = {}
        for item in ITEM_TYPES:
            try:
                self.item_graphics[item] = pygame.image.load(f'graphics/items/heart.png').convert_alpha()
                self.item_graphics[item] = pygame.transform.scale(self.item_graphics[item], (50, 50)) # ubah ukuran inventory di pojok kiri
            except:
                # Create default item graphics
                surf = pygame.Surface((32, 32))
                if item == 'coin':
                    surf.fill((255, 215, 0))
                elif item == 'key':
                    surf.fill((192, 192, 192))
                elif item == 'potion':
                    surf.fill((255, 0, 255))
                self.item_graphics[item] = surf

        # Untuk tampilan kamera
        self.camera_object = None # Akan diisi dengan objek kamera HandGestureCamera
        self.show_camera_feed = True # Kontrol untuk menampilkan atau menyembunyikan feed kamera

    def set_camera(self, camera_instance):
        """Mengatur instance kamera yang akan digunakan oleh UI."""
        self.camera_object = camera_instance

    def toggle_camera_feed(self):
        """Mengubah status tampil/sembunyi feed kamera."""
        self.show_camera_feed = not self.show_camera_feed

    def display_camera_feed(self): # Mengganti nama dari show_camera ke display_camera_feed agar lebih jelas
        """Menampilkan feed kamera di pojok kanan atas."""
        # Menggunakan self.camera_object yang sudah di-set dan self.show_camera_feed
        if self.camera_object and self.show_camera_feed:
            try:
                cam_surface = self.camera_object.get_frame() #
                if cam_surface:
                    # Menggunakan self.display_surface yang sudah ada di __init__
                    rect = cam_surface.get_rect(topright=(self.display_surface.get_width() - 10, 10))
                    self.display_surface.blit(cam_surface, rect)
                    pygame.draw.rect(self.display_surface, (255, 255, 255), rect, 2) # Border putih
            except Exception as e:
                print(f"Error displaying camera feed: {e}") # Pesan error jika ada masalah
                pass

    def show_inventory(self, inventory):
        """Menampilkan inventaris pemain."""
        x, y = 20, 20 #
        for index, (item, amount) in enumerate(inventory.items()): #
            item_image = self.item_graphics.get(item, None) #
            if item_image: #
                item_rect = item_image.get_rect(topleft=(x, y + index * 50)) #
                pygame.draw.rect(self.display_surface, UI_BG_COLOR, item_rect.inflate(20, 20)) #
                self.display_surface.blit(item_image, item_rect) #
                pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, item_rect.inflate(20, 20), 3) #
                
                # Draw amount text
                amount_text = self.font.render(' ' + 'x' + ' ' + f'{amount}', False, (255, 255, 255)) #
                amount_rect = amount_text.get_rect(midleft=(item_rect.right + 10, item_rect.centery)) #
                self.display_surface.blit(amount_text, amount_rect) #

    def display(self, player): # Player mungkin bisa None jika game baru mulai atau state lain
        """Menampilkan semua elemen UI."""
        if player and hasattr(player, 'inventory'):
            self.show_inventory(player.inventory) #
        
        self.display_camera_feed() # Panggil metode untuk menampilkan feed kamera