import pygame
import math
from settings import *

from camera import HandGestureCamera

class UI:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.font = pygame.font.Font(None, 30)
        
        # Load item graphics
        self.item_graphics = {}
        for item in ITEM_TYPES:
            try:
                # Assuming all items for now use the heart graphic for simplicity
                graphic_path = 'graphics/items/heart.png'
                self.item_graphics[item] = pygame.image.load(graphic_path).convert_alpha()
                self.item_graphics[item] = pygame.transform.scale(self.item_graphics[item], (50, 50))
            except Exception as e:
                print(f"Could not load graphic for {item}: {e}. Creating placeholder.")
                surf = pygame.Surface((32, 32))
                surf.fill('red')
                self.item_graphics[item] = surf

        # Camera display
        self.camera_object = None
        self.show_camera_feed = True
        
        # Dwell clock properties
        self.clock_radius = 25
        self.clock_bg_color = '#444444'
        self.clock_fg_color = '#00FF7F' # SpringGreen
        self.clock_width = 6

    def set_camera(self, camera_instance):
        """Sets the camera instance to be used by the UI."""
        self.camera_object = camera_instance

    def toggle_camera_feed(self):
        """Toggles the visibility of the camera feed."""
        self.show_camera_feed = not self.show_camera_feed

    def display_camera_feed(self):
        """Displays the camera feed in the top-right corner."""
        if self.camera_object and self.show_camera_feed:
            try:
                cam_surface = self.camera_object.get_frame()
                if cam_surface:
                    cam_rect = cam_surface.get_rect(topright=(self.display_surface.get_width() - 10, 10))
                    self.display_surface.blit(cam_surface, cam_rect)
                    pygame.draw.rect(self.display_surface, (255, 255, 255), cam_rect, 2)
                    
                    # Return the rect so the dwell clock can position itself
                    return cam_rect
            except Exception as e:
                print(f"Error displaying camera feed: {e}")
        return None

    def display_dwell_clock(self, camera_rect):
        """
        Displays a circular progress bar under the camera feed to show dwell time.
        """
        if self.camera_object and camera_rect:
            progress = self.camera_object.get_dwell_progress()
            if progress > 0:
                # Calculate position for the clock
                clock_center = (camera_rect.centerx, camera_rect.bottom + self.clock_radius + 15)
                
                # Draw the background circle
                pygame.draw.circle(self.display_surface, self.clock_bg_color, clock_center, self.clock_radius, self.clock_width)
                
                # Draw the foreground arc
                if progress < 1.0:
                    start_angle = math.pi / 2
                    end_angle = start_angle - (progress * 2 * math.pi)
                    pygame.draw.arc(self.display_surface, self.clock_fg_color, 
                                    (clock_center[0] - self.clock_radius, clock_center[1] - self.clock_radius, self.clock_radius * 2, self.clock_radius * 2), 
                                    end_angle, start_angle, self.clock_width)
                else: # Draw full circle when complete
                    pygame.draw.circle(self.display_surface, self.clock_fg_color, clock_center, self.clock_radius, self.clock_width)


    def show_inventory(self, inventory, target):
        """Displays the player's inventory."""
        x, y = 20, 20
        for index, (item, amount) in enumerate(inventory.items()):
            item_image = self.item_graphics.get(item)
            if item_image:
                item_rect = item_image.get_rect(topleft=(x, y + index * 60))
                
                # Background box for the item icon
                bg_rect = item_rect.inflate(20, 20)
                pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_rect, border_radius=5)
                
                # Blit the item icon
                self.display_surface.blit(item_image, item_rect)
                
                # Border for the item icon
                pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_rect, 3, border_radius=5)
                
                # --- Amount text with its own background ---
                display_text = f'{amount} / {target}'
                amount_text = self.font.render(display_text, False, TEXT_COLOR)
                amount_rect = amount_text.get_rect(midleft=(item_rect.right + 10, item_rect.centery))

                # Create and draw the background for the text
                bg_text_rect = amount_rect.inflate(10, 10)
                pygame.draw.rect(self.display_surface, UI_BG_COLOR, bg_text_rect, border_radius=5)
                
                # Draw the text itself
                self.display_surface.blit(amount_text, amount_rect)

                # Draw the border for the text's background
                pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, bg_text_rect, 3, border_radius=5)

    def display(self, player, target):
        """Displays all UI elements."""
        if player and hasattr(player, 'inventory'):
            self.show_inventory(player.inventory, target)
        
        camera_rect = self.display_camera_feed()
        self.display_dwell_clock(camera_rect)
