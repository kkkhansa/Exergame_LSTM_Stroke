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
        pass


class Level:
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

        self.hearts_to_collect = 1 # change as needed for the level
        self.level_complete = False
        self.proceed_to_next_level = False

        self.manual_gesture_input_mode = False

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
            'heart': pygame.transform.scale(pygame.image.load("graphics/items/heart.png").convert_alpha(), (TILESIZE, TILESIZE))
        }

        for style,layout in layouts.items():
            for row_index,row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILESIZE
                        y = row_index * TILESIZE
                        if style == 'boundary':
                            Tile((x,y),[self.obstacle_sprites],'invisible')
                        elif style == 'grass':
                            Tile((x,y), [self.visible_sprites,self.obstacle_sprites], 'grass', choice(graphics['grass']))
                        elif style == 'object':
                            Tile((x,y),[self.visible_sprites,self.obstacle_sprites],'object',graphics['objects'][int(col)])
                        elif style == 'entities':
                            if col == '394': 
                                self.player = Player(pos=(x + TILESIZE // 2, y + TILESIZE // 2), groups=[self.visible_sprites], obstacle_sprites=self.obstacle_sprites, camera_input=self.game_camera)
                            elif col in ['390', '391', '392', '393']: 
                                Item((x + TILESIZE // 2, y + TILESIZE // 2), [self.visible_sprites, self.item_sprites], 'heart', graphics['heart'])
    
    def player_item_collection_logic(self):
        if self.player and not self.level_complete:
            collided_items = pygame.sprite.spritecollide(self.player, self.item_sprites, True)
            for item_sprite in collided_items:
                self.player.collect_item(item_sprite.item_type)
                if self.player.inventory.get('heart', 0) >= self.hearts_to_collect:
                    self.level_complete = True
                    print("Level 1 Objective Achieved!")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.manual_gesture_input_mode = not self.manual_gesture_input_mode
                print(f"MANUAL GESTURE MODE: {'ENABLED' if self.manual_gesture_input_mode else 'DISABLED (using camera)'}")
            
            if self.manual_gesture_input_mode:
                if event.key in [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3]:
                    action_label = int(pygame.key.name(event.key))
                    if self.player:
                        self.player.execute_gesture_move(action_label)

    def show_level_complete_screen(self):
        frozen_surface = self.display_surface.copy()
        title_font = self.font_renderer.get_font(60) 
        button_font = self.font_renderer.get_font(50)

        while True:
            self.display_surface.blit(frozen_surface, (0,0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.display_surface.blit(overlay, (0,0))

            mouse_pos = pygame.mouse.get_pos()

            complete_text = title_font.render("Level 1 Complete!", True, 'white')
            complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            self.display_surface.blit(complete_text, complete_rect)

            proceed_button = Button(pos=(WIDTH // 2, HEIGHT // 2 + 50), text="Next Level", font=button_font, base_color="white", hover_color="lightgreen")
            proceed_button.change_color(mouse_pos)
            proceed_button.draw(self.display_surface)
            
            menu_button = Button(pos=(WIDTH // 2, HEIGHT // 2 + 150), text="Main Menu", font=button_font, base_color="white", hover_color="lightblue")
            menu_button.change_color(mouse_pos)
            menu_button.draw(self.display_surface)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if proceed_button.check_click(mouse_pos):
                        self.proceed_to_next_level = True
                        return "LEVEL_COMPLETE_PROCEED" 
                    if menu_button.check_click(mouse_pos):
                        return "RETURN_TO_MENU"
            
            pygame.display.update()

    def run(self):
        if self.level_complete:
            action = self.show_level_complete_screen()
            return action if action else "RUNNING"

        if not self.game_paused:
            # --- New Dwell Time Logic ---
            gesture_action = None
            if self.game_camera and self.player and self.player.control_with_gesture and not self.manual_gesture_input_mode:
                self.game_camera.process()
                gesture_action = self.game_camera.consume_action()

            if gesture_action is not None:
                self.player.execute_gesture_move(gesture_action)

            self.visible_sprites.update() 
            self.player_item_collection_logic()
        
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
        for sprite in self.sprites():
            sprite.update(**kwargs)
