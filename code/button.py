import pygame

class Button:
    def __init__(self, pos, text, font, base_color, hover_color):
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_surface = self.font.render(self.text, True, self.base_color)
        self.rect = self.text_surface.get_rect(center=pos)
        
        # Create button background
        self.bg_rect = self.rect.inflate(40, 20)

    def draw(self, screen):
        # Draw button background
        pygame.draw.rect(screen, (50, 50, 50), self.bg_rect)
        pygame.draw.rect(screen, self.hover_color if self.is_hovered else (100, 100, 100), self.bg_rect, 3)
        screen.blit(self.text_surface, self.rect)

    def check_click(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def change_color(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if self.is_hovered else self.base_color
        self.text_surface = self.font.render(self.text, True, color)
