import pygame
import sys 
from settings import *
from tile import Tile
from level.player import Player 
from level.support import * 
from random import choice
from ui import UI
from button import Button 

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
                   self.image = pygame.transform.scale(pygame.image.load('graphics/items/heart.png').convert_alpha(), (TILESIZE, TILESIZE))
               except pygame.error as e:
                   print(f"Error loading heart item image: {e}. Using placeholder.")
                   self.image.fill('red') 
            else:
                self.image.fill('grey')
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(0, 0)

    def update(self, **kwargs):
        # Added **kwargs to accept extra arguments from group.update() calls
        pass

class TrialLevel:
    def __init__(self, camera_instance, screen_surface, font_renderer):
        self.display_surface = screen_surface
        self.font_renderer = font_renderer
        self.game_paused = False

        self.visible_sprites = YSortCameraGroup(self.display_surface)
        self.obstacle_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()

        self.game_camera = camera_instance 
        self.player = None 
        self.create_map() 

        self.ui = UI()
        if self.game_camera:
            self.ui.set_camera(self.game_camera) 

        self.hearts_to_collect = float('inf') # Number of hearts to collect in this level
        # --- Manual Gesture Input for Debugging ---
        self.manual_gesture_input_mode = False # Start with camera mode by default
        self.last_manual_label = 5 
        self.awaiting_manual_gesture_input = False

    def create_map(self):
        layouts = {'boundary': import_csv_layout("map/map_FloorBlocks.csv"), 'grass': import_csv_layout("map/map_Grass.csv"), 'object': import_csv_layout("map/map_Objects.csv"), 'entities': import_csv_layout("map/map_Entities.csv")}
        graphics = {'grass': import_folder("graphics/grass"), 'objects': import_folder("graphics/objects"), 'heart': pygame.transform.scale(pygame.image.load("graphics/items/heart.png").convert_alpha(), (TILESIZE, TILESIZE))}

        for style,layout in layouts.items():
            for row_index,row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x, y = col_index * TILESIZE, row_index * TILESIZE
                        if style == 'boundary': Tile((x,y),[self.obstacle_sprites],'invisible')
                        if style == 'grass': Tile((x,y), [self.visible_sprites,self.obstacle_sprites], 'grass', choice(graphics['grass']))
                        if style == 'object': Tile((x,y),[self.visible_sprites,self.obstacle_sprites],'object',graphics['objects'][int(col)])
                        if style == 'entities':
                            if col == '394': 
                                self.player = Player(pos=(x + TILESIZE // 2, y + TILESIZE // 2), groups=[self.visible_sprites], obstacle_sprites=self.obstacle_sprites, camera_input=self.game_camera)
                            elif col in ['390', '391', '392', '393']: 
                                Item((x + TILESIZE // 2, y + TILESIZE // 2), [self.visible_sprites, self.item_sprites], 'heart', graphics['heart'])
    
    def player_item_collection_logic(self):
        if self.player:
            collided_items = pygame.sprite.spritecollide(self.player, self.item_sprites, True)
            for item_sprite in collided_items:
                if hasattr(self.player, 'collect_item'):
                    self.player.collect_item(item_sprite.item_type)

    def handle_event(self, event):
        """Handles events like toggling manual input."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.manual_gesture_input_mode = not self.manual_gesture_input_mode
                print(f"MANUAL GESTURE MODE: {'ENABLED' if self.manual_gesture_input_mode else 'DISABLED (using camera)'}")
                if self.manual_gesture_input_mode:
                    print("Focus Pygame window and press a number key (0-3) to trigger a one-time move.")
            
            # If in manual mode, listen for number keys
            if self.manual_gesture_input_mode:
                if event.key in [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3]:
                    action_label = int(pygame.key.name(event.key))
                    print(f"Manual action triggered: {action_label}")
                    if self.player:
                        self.player.execute_gesture_move(action_label)

    def run(self):
        # --- Process Camera and Get Confirmed Actions ---
        gesture_action = None
        if self.game_camera and not self.manual_gesture_input_mode:
            self.game_camera.process()
            gesture_action = self.game_camera.consume_action()

        # If an action was confirmed by the camera, tell the player to execute it
        if self.player and gesture_action is not None:
            self.player.execute_gesture_move(gesture_action)
        
        # --- Update Game State ---
        # This will call player.update() which handles keyboard input
        self.visible_sprites.update() 
        self.player_item_collection_logic()
        
        # --- Drawing ---
        self.visible_sprites.custom_draw(self.player)
        if hasattr(self, 'ui') and self.player: 
            self.ui.display(self.player, self.hearts_to_collect)
        
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
            print(f"Error loading background image: {e}. Creating fallback.")
            self.floor_surf = pygame.Surface(self.display_surface.get_size())
            self.floor_surf.fill((30,30,30)) 
        self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

    def custom_draw(self,player):
        if player:
            self.offset.x = player.rect.centerx - self.half_width
            self.offset.y = player.rect.centery - self.half_height
        
        floor_offset_pos = self.floor_rect.topleft - self.offset
        self.display_surface.blit(self.floor_surf,floor_offset_pos)

        for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image,offset_pos)
            
    def update(self, **kwargs):
        # Override group's update to pass down arguments
        for sprite in self.sprites():
            sprite.update(**kwargs)
