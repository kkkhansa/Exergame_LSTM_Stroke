import pygame
import sys
from settings import *
from tile import Tile
from level.player import Player # Assuming player.py is in the 'level' folder
from level.support import * # Assuming support.py is in the 'level' folder
from random import choice
from ui import UI
from button import Button

# Kelas Item Sederhana (sama seperti di level1.py)
class Item(pygame.sprite.Sprite):
    def __init__(self, pos, groups, item_type, surface=None):
        super().__init__(groups)
        self.sprite_type = 'item'
        self.item_type = item_type
        
        if surface:
            self.image = surface
        else:
            self.image = pygame.Surface((TILESIZE, TILESIZE)) 
            if self.item_type == 'heart':
               try:
                   loaded_image = pygame.image.load('graphics/items/heart.png').convert_alpha()
                   self.image = pygame.transform.scale(loaded_image, (TILESIZE, TILESIZE))
               except pygame.error as e:
                   print(f"Error loading heart item image in Item fallback (Trial): {e}. Using placeholder.")
                   self.image.fill('red') 
            else:
                self.image.fill('grey')
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(0, 0)

class TrialLevel: # Renamed class to TrialLevel
    def __init__(self, camera_instance, screen_surface, font_renderer):
        self.display_surface = screen_surface
        self.font_renderer = font_renderer # For potential future use, not strictly needed if no complete screen
        self.game_paused = False # Internal pause state, main.py handles game-wide pause state

        self.visible_sprites = YSortCameraGroup(self.display_surface)
        self.obstacle_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()

        self.game_camera = camera_instance
        self.player = None 
        self.create_map() 

        self.ui = UI()
        if self.game_camera:
            self.ui.set_camera(self.game_camera)

        # No specific item collection goal for trial level
        # self.hearts_to_collect = X 
        # self.level_complete = False
        # self.proceed_to_next_level = False

        if self.player:
            if not hasattr(self.player, 'inventory') or not isinstance(self.player.inventory, dict):
                self.player.inventory = {'heart': 0}
            elif 'heart' not in self.player.inventory: # Ensure 'heart' key exists
                self.player.inventory['heart'] = 0
        else:
            print("TRIAL LEVEL WARNING: Player object not created after create_map().")

    def create_map(self):
        # Using the same map layout as Level 1 for simplicity
        # You can change these paths if you have a specific map for the trial level
        layouts = {
            'boundary': import_csv_layout("map/map_FloorBlocks.csv"),
            'grass': import_csv_layout("map/map_Grass.csv"),
            'object': import_csv_layout("map/map_Objects.csv"),
            'entities': import_csv_layout("map/map_Entities.csv")
        }
        graphics = {
            'grass': import_folder("graphics/grass"),
            'objects': import_folder("graphics/objects"),
            'heart': pygame.transform.scale(
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
                                    # camera_input=self.game_camera # Pass camera if Player needs it
                                )
                                if not hasattr(self.player, 'inventory') or not isinstance(self.player.inventory, dict):
                                    self.player.inventory = {'heart': 0}
                                elif 'heart' not in self.player.inventory:
                                     self.player.inventory['heart'] = 0
                            # Items can still exist and be collected, but no goal attached
                            elif col in ['390', '391', '392', '393']: 
                                Item(
                                    (x + TILESIZE // 2, y + TILESIZE // 2),
                                    [self.visible_sprites, self.item_sprites],
                                    'heart',
                                    graphics['heart']
                                )
    
    def player_item_collection_logic(self):
        # Player can collect items, but it doesn't trigger level completion
        if self.player:
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
                    print(f"Trial: Collected heart! Total: {self.player.inventory.get('heart', 0)}")
                    # No check for self.hearts_to_collect or setting self.level_complete

    # toggle_menu is not strictly needed if main.py handles pause state changes
    # def toggle_menu(self):
    #     self.game_paused = not self.game_paused
    #     return "PAUSE_MENU_REQUESTED" 

    # show_level_complete_screen is not needed for trial level
    # def show_level_complete_screen(self): ...

    def run(self):
        # Trial level runs until paused and exited via main.py's pause menu.
        # It doesn't have its own "complete" state that leads to another level.

        # Logika game berjalan normal jika tidak di-pause (main.py's game_paused)
        # self.game_paused (internal level pause) is not used here as main.py controls overall pause
        
        if self.game_camera and self.player:
            if hasattr(self.player, 'control_with_gesture') and self.player.control_with_gesture:
                self.game_camera.process() 
                predicted_label = self.game_camera.get_predicted_label()
                if hasattr(self.player, 'set_predicted_gesture_label'):
                    self.player.set_predicted_gesture_label(predicted_label)
                else:
                    self.player.predicted_label = predicted_label
        
        self.visible_sprites.update() 
        if self.player:
            self.player_item_collection_logic()
        
        self.visible_sprites.custom_draw(self.player)
        if hasattr(self, 'ui') and self.player:
            self.ui.display(self.player)
        
        # TrialLevel's run method will be called repeatedly by main.py's PLAYING_LEVEL state.
        # If main.py changes state (e.g., to PAUSE_MENU or MENU), then this run loop effectively ends for TrialLevel.
        # It doesn't need to return a special "complete" status.
        # "PAUSED" can be returned if an in-level event triggers a pause, but K_ESCAPE is handled by main.py
        return "RUNNING" 


class YSortCameraGroup(pygame.sprite.Group):
    def __init__(self, display_surface):
        super().__init__()
        self.display_surface = display_surface
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

        try:
            self.floor_surf = pygame.image.load("graphics/tilemap/Background.png").convert()
        except pygame.error as e:
            print(f"Error loading background image for YSortCameraGroup (Trial): {e}. Creating fallback.")
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
