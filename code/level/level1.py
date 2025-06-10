import pygame
import sys # Diperlukan untuk sys.exit() di layar transisi
from settings import *
from tile import Tile
from level.player import Player
from level.support import *
from random import choice
from ui import UI
from button import Button # Impor kelas Button

# Kelas Item Sederhana (tidak berubah dari sebelumnya)
class Item(pygame.sprite.Sprite):
    def __init__(self, pos, groups, item_type, surface=None):
        super().__init__(groups)
        self.sprite_type = 'item'
        self.item_type = item_type
        
        if surface: # Gambar sudah diskalakan di create_map
            self.image = surface
        else:
            # Fallback jika surface tidak disediakan
            self.image = pygame.Surface((TILESIZE, TILESIZE)) 
            if self.item_type == 'heart':
               try:
                   loaded_image = pygame.image.load('graphics/items/heart.png').convert_alpha()
                   self.image = pygame.transform.scale(loaded_image, (TILESIZE, TILESIZE))
               except pygame.error as e:
                   print(f"Error loading heart item image in Item fallback: {e}. Using placeholder.")
                   self.image.fill('red') 
            else:
                self.image.fill('grey')
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(0, 0)


class Level:
    def __init__(self, camera_instance, screen_surface, font_renderer): # Tambahkan screen dan font
        self.display_surface = screen_surface # Gunakan screen yang dioper
        self.font_renderer = font_renderer # Gunakan font renderer yang dioper
        self.game_paused = False

        self.visible_sprites = YSortCameraGroup(self.display_surface) # Oper display_surface
        self.obstacle_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()

        self.game_camera = camera_instance

        self.player = None 
        self.create_map() 

        self.ui = UI() # UI akan menggunakan display_surface dari pygame.display.get_surface() secara internal
        if self.game_camera:
            self.ui.set_camera(self.game_camera)

        # Tujuan Level
        self.hearts_to_collect = 2 # Tujuan untuk Level 1
        self.level_complete = False
        self.proceed_to_next_level = False # Flag untuk memberi tahu main.py

        if self.player:
            if not hasattr(self.player, 'inventory') or not isinstance(self.player.inventory, dict):
                self.player.inventory = {'heart': 0}
            elif 'heart' not in self.player.inventory:
                self.player.inventory['heart'] = 0
        else:
            print("LEVEL WARNING: Player object not created after create_map().")

        # --- Manual Gesture Input for Debugging (from trial.py) ---
        self.manual_gesture_input_mode = True 
        self.last_manual_label = 5 # Default to Idle (label 5)
        self.awaiting_manual_gesture_input = False # New flag

        if self.manual_gesture_input_mode:
            print("-" * 30)
            print("MANUAL GESTURE INPUT MODE ENABLED FOR LEVEL 1")
            print("Focus Pygame window, press 'M' to trigger terminal input prompt.")
            print("Player Gesture Labels (Ensure player.py matches this):")
            print("  0: Up -> open palm")
            print("  1: Right -> thumb_index")
            print("  2: Down -> closed fist")
            print("  3: Left -> grabbing")
            print("  5: Idle / No specific gesture")
            print("-" * 30)
        # --- End Manual Gesture Input ---

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
            'heart': pygame.transform.scale( # Skala dilakukan di sini
                pygame.image.load("graphics/items/heart.png").convert_alpha(),
                (TILESIZE, TILESIZE) 
            )
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
                            if col == '394': 
                                self.player = Player(
                                    pos=(x + TILESIZE // 2, y + TILESIZE // 2),
                                    groups=[self.visible_sprites],
                                    obstacle_sprites=self.obstacle_sprites,
                                    camera_input=self.game_camera
                                )
                                if not hasattr(self.player, 'inventory') or not isinstance(self.player.inventory, dict):
                                    self.player.inventory = {'heart': 0}
                                elif 'heart' not in self.player.inventory:
                                     self.player.inventory['heart'] = 0

                            elif col in ['390', '391', '392', '393']: 
                                Item(
                                    (x + TILESIZE // 2, y + TILESIZE // 2),
                                    [self.visible_sprites, self.item_sprites],
                                    'heart',
                                    graphics['heart']
                                )
    
    def player_item_collection_logic(self):
        if self.player and not self.level_complete: # Hanya proses jika level belum selesai
            collided_items = pygame.sprite.spritecollide(self.player, self.item_sprites, True)
            for item_sprite in collided_items:
                if item_sprite.item_type == 'heart':
                    if hasattr(self.player, 'collect_item'):
                        self.player.collect_item('heart')
                    else: 
                        if 'heart' in self.player.inventory:
                            self.player.inventory['heart'] += 1
                        else:
                            self.player.inventory['heart'] = 1
                    print(f"Collected heart! Total: {self.player.inventory.get('heart', 0)}")

                    # Cek apakah tujuan tercapai
                    if self.player.inventory.get('heart', 0) >= self.hearts_to_collect:
                        self.level_complete = True
                        print("Level 1 Objective Achieved!")
                        # Jangan langsung tampilkan layar di sini, biarkan run() yang mengelola state

    def handle_event(self, event):
        """Handles events specifically for the level, like toggling manual input."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                if self.manual_gesture_input_mode:
                    self.awaiting_manual_gesture_input = True
                    print("Level 1: 'M' pressed. Will prompt for label in terminal at start of next run() cycle.")
                else: 
                    self.manual_gesture_input_mode = True
                    print("MANUAL GESTURE INPUT MODE ENABLED. Press 'M' in Pygame window to input label. Press 'N' to use camera.")
                    if self.game_camera:
                         self.last_manual_label = self.game_camera.get_predicted_label()
                    else:
                        self.last_manual_label = 5 
            elif event.key == pygame.K_n:
                if self.manual_gesture_input_mode:
                    self.manual_gesture_input_mode = False
                    self.awaiting_manual_gesture_input = False
                    print("MANUAL GESTURE INPUT MODE DISABLED. Using camera.")

    def toggle_menu(self): # Untuk menu pause
        self.game_paused = not self.game_paused
        return "PAUSE_MENU_REQUESTED" # Memberi tahu main.py untuk menampilkan menu pause

    def show_level_complete_screen(self):
        """Menampilkan layar saat level selesai, mirip pause menu."""
        frozen_surface = self.display_surface.copy() # Bekukan layar game saat ini
        
        title_font = self.font_renderer.get_font(60) 
        button_font = self.font_renderer.get_font(50)

        while True:
            self.display_surface.blit(frozen_surface, (0,0))
            
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) # Hitam dengan alpha 180
            self.display_surface.blit(overlay, (0,0))

            mouse_pos = pygame.mouse.get_pos()

            complete_text = title_font.render("Level 1 Complete!", True, 'white')
            complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            self.display_surface.blit(complete_text, complete_rect)

            proceed_button = Button(
                pos=(WIDTH // 2, HEIGHT // 2 + 50),
                text="Next Level",
                font=button_font,
                base_color="white",
                hover_color="lightgreen"
            )
            proceed_button.change_color(mouse_pos)
            proceed_button.draw(self.display_surface)
            
            menu_button = Button(
                pos=(WIDTH // 2, HEIGHT // 2 + 150),
                text="Main Menu",
                font=button_font,
                base_color="white",
                hover_color="lightblue"
            )
            menu_button.change_color(mouse_pos)
            menu_button.draw(self.display_surface)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if proceed_button.check_click(mouse_pos):
                        self.proceed_to_next_level = True
                        return "PROCEED_LEVEL_2" 
                    if menu_button.check_click(mouse_pos):
                        return "RETURN_TO_MENU"
            
            pygame.display.update()

    def run(self):
        if self.level_complete and not self.proceed_to_next_level:
            action = self.show_level_complete_screen()
            if action == "PROCEED_LEVEL_2":
                return "LEVEL_COMPLETE_PROCEED" 
            elif action == "RETURN_TO_MENU":
                return "RETURN_TO_MENU"

        if self.proceed_to_next_level:
            return "LEVEL_COMPLETE_PROCEED"

        if not self.game_paused:
            # --- Manual Input Prompt (from trial.py) ---
            if self.manual_gesture_input_mode and self.awaiting_manual_gesture_input:
                try:
                    print("-" * 10)
                    raw_label = input(f"Enter gesture label (current: {self.last_manual_label}, 0:Up, 1:Right, 2:Down, 3:Left, 5:Idle): ")
                    self.last_manual_label = int(raw_label)
                    print(f"Manual label set to: {self.last_manual_label}")
                except ValueError:
                    print("Invalid input. Please enter a number. Using previous label.")
                except Exception as e:
                    print(f"Error during manual input: {e}. Using previous label.")
                finally:
                    self.awaiting_manual_gesture_input = False 

            # --- Determine Predicted Label (from trial.py) ---
            predicted_label_for_player = 5 # Default to Idle
            if self.manual_gesture_input_mode:
                predicted_label_for_player = self.last_manual_label
            elif self.game_camera: 
                self.game_camera.process() 
                predicted_label_for_player = self.game_camera.get_predicted_label()
            
            # --- Update Player with Label (from trial.py) ---
            if self.player:
                if hasattr(self.player, 'set_predicted_gesture_label'):
                    self.player.set_predicted_gesture_label(predicted_label_for_player)
                else: 
                    self.player.predicted_label = predicted_label_for_player
            
            self.visible_sprites.update() 
            if self.player:
                self.player_item_collection_logic()
        
        self.visible_sprites.custom_draw(self.player)
        if hasattr(self, 'ui') and self.player:
            self.ui.display(self.player)
        
        if self.game_paused: 
            return "PAUSED"
            
        return "RUNNING"


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self, display_surface): # Terima display_surface
        super().__init__()
        self.display_surface = display_surface # Gunakan surface yang dioper
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

        try:
            self.floor_surf = pygame.image.load("graphics/tilemap/Background.png").convert()
        except pygame.error as e:
            print(f"Error loading background image for YSortCameraGroup: {e}. Creating fallback.")
            self.floor_surf = pygame.Surface((self.display_surface.get_width(), self.display_surface.get_height()))
            self.floor_surf.fill((30,30,30)) 
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