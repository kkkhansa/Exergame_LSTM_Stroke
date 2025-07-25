import pygame, sys
import os
from button import Button
from settings import *

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font("graphics/font/joystix.ttf", 45) if os.path.exists("graphics/font/joystix.ttf") else pygame.font.Font(None, 45)
        
        # Load background image (fallback to gradient if not found)
        try:
            self.background = pygame.image.load("graphics/tilemap/Background.png")
            self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))
        except:
            # Create gradient background as fallback
            self.background = self.create_gradient_background()

    def create_gradient_background(self):
        """Create a gradient background if image not found"""
        surface = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            color_intensity = int(255 * (y / HEIGHT))
            color = (color_intensity // 4, color_intensity // 3, color_intensity // 2)
            pygame.draw.line(surface, color, (0, y), (WIDTH, y))
        return surface

    def get_font(self, size):
        if os.path.exists("graphics/font/joystix.ttf"):
            return pygame.font.Font("graphics/font/joystix.ttf", size)
        return pygame.font.Font(None, size)

    def show_main_menu(self):
        while True:
            # Draw background
            self.screen.blit(self.background, (0, 0))
            
            mouse_pos = pygame.mouse.get_pos()

            title = self.get_font(80).render("MAIN MENU", True, TEXT_COLOR_SELECTED)
            title_rect = title.get_rect(center=(WIDTH//2, 100))
            
            # Add shadow effect to title
            shadow = self.get_font(80).render("MAIN MENU", True, (50, 50, 50))
            self.screen.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
            self.screen.blit(title, title_rect)

            play_button = Button((WIDTH//2, 250), "PLAY", self.get_font(50), "white", "green")
            levels_button = Button((WIDTH//2, 375), "LEVELS", self.get_font(50), "white", "blue")
            quit_button = Button((WIDTH//2, 500), "QUIT", self.get_font(50), "white", "red")

            for button in [play_button, levels_button, quit_button]:
                button.change_color(mouse_pos)
                button.draw(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if play_button.check_click(mouse_pos):
                        return "PLAY"
                    if levels_button.check_click(mouse_pos):
                        return "LEVELS"
                    if quit_button.check_click(mouse_pos):
                        return "QUIT"

            pygame.display.update()

    def show_pause_menu(self, frozen_surface=None):
        while True:
            # Draw the frozen game screen if provided
            if frozen_surface:
                self.screen.blit(frozen_surface, (0, 0))
                # Add semi-transparent overlay
                overlay = pygame.Surface((WIDTH, HEIGHT))
                overlay.set_alpha(128)
                overlay.fill((0, 0, 0))
                self.screen.blit(overlay, (0, 0))
            else:
                self.screen.fill("gray")
            
            mouse_pos = pygame.mouse.get_pos()

            # Pause menu title
            pause_title = self.get_font(60).render("PAUSED", True, "white")
            pause_rect = pause_title.get_rect(center=(WIDTH//2, 150))
            self.screen.blit(pause_title, pause_rect)

            resume_button = Button((WIDTH//2, 250), "RESUME", self.get_font(50), "white", "green")
            menu_button = Button((WIDTH//2, 400), "MENU", self.get_font(50), "white", "yellow")

            for button in [resume_button, menu_button]:
                button.change_color(mouse_pos)
                button.draw(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "RESUME"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if resume_button.check_click(mouse_pos):
                        return "RESUME"
                    if menu_button.check_click(mouse_pos):
                        return "MENU"

            pygame.display.update()

    def show_levels_menu(self):
        while True:
            self.screen.fill("black")
            mouse_pos = pygame.mouse.get_pos()

            title = self.get_font(80).render("LEVELS", True, 'white')
            title_rect = title.get_rect(center=(WIDTH//2, 100))
            self.screen.blit(title, title_rect)

            # Placeholder buttons for levels
            trial_button = Button((WIDTH//2, 200), "TRIAL", self.get_font(50), "white", "green")
            level1_button = Button((WIDTH//2, 300), "LEVEL 1", self.get_font(50), "white", "blue")
            level2_button = Button((WIDTH//2, 400), "LEVEL 2", self.get_font(50), "white", "blue")
            back_button = Button((WIDTH//2, 600), "BACK", self.get_font(50), "white", "red")

            for button in [trial_button, level1_button, level2_button, back_button]:
                button.change_color(mouse_pos)
                button.draw(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if trial_button.check_click(mouse_pos):
                        return "TRIAL"
                    if level1_button.check_click(mouse_pos):
                        return "LEVEL_1"
                    if level2_button.check_click(mouse_pos):
                        return "LEVEL_2"
                    if back_button.check_click(mouse_pos):
                        return "BACK"

            pygame.display.update()






