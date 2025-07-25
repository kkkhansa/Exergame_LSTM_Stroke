import pygame, sys
import threading # --- PERUBAHAN UNTUK DEBUGGING ---
from settings import *
from main_menu import MainMenu
from level.level1 import Level as Level1
from level.level2 import Level as Level2
from level.trial import TrialLevel
from camera import HandGestureCamera # Pastikan Anda menggunakan versi debug dari kamera
from camera_debug import GameDebugger # --- PERUBAHAN UNTUK DEBUGGING ---

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Heart Collector')
        self.clock = pygame.time.Clock()
        
        self.current_game_state = "MENU"
        self.active_level_instance = None

        self.camera = HandGestureCamera()
        self.main_menu = MainMenu(self.screen)
        
        # --- PERUBAHAN UNTUK DEBUGGING ---
        # Buat instance debugger dan berikan akses ke instance kamera
        self.debugger = GameDebugger(self.camera)
        # --------------------------------

        self.level_definitions = {
            "TRIAL": TrialLevel,
            "LEVEL_1": Level1,
            "LEVEL_2": Level2,
        }
        self.current_level_key = None

    # ... (Metode start_level tidak perlu diubah) ...
    def start_level(self, level_key):
        if level_key in self.level_definitions:
            self.current_level_key = level_key
            self.active_level_instance = self.level_definitions[level_key](
                camera_instance=self.camera,
                screen_surface=self.screen,
                font_renderer=self.main_menu
            )
            self.current_game_state = "PLAYING_LEVEL"
            print(f"Starting {level_key}")
        else:
            print(f"Error: Level key '{level_key}' not found in definitions.")
            self.current_game_state = "MENU"


    def run(self):
        # --- PERUBAHAN UNTUK DEBUGGING ---
        # Jalankan debugger di thread terpisah
        self.debugger.start()
        # --------------------------------
        
        while True:
            # --- PERUBAHAN UNTUK DEBUGGING ---
            # Berikan data FPS game ke instance kamera agar debugger bisa membacanya
            # Ini lebih akurat daripada menghitung FPS di dalam thread debug itu sendiri
            current_fps = self.clock.get_fps()
            self.camera.game_fps = current_fps # Anda perlu menambahkan atribut ini di camera_debug.py
            # --------------------------------

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Cleanup akan ditangani di blok finally di bawah
                    pygame.quit()
                    sys.exit()
                
                if self.active_level_instance and hasattr(self.active_level_instance, 'handle_event'):
                    self.active_level_instance.handle_event(event)
                
                if self.current_game_state == "PLAYING_LEVEL" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.last_game_surface_before_pause = self.screen.copy()
                        self.current_game_state = "PAUSE_MENU"

            # State machine (tidak ada perubahan di sini)
            if self.current_game_state == "MENU":
                menu_action = self.main_menu.show_main_menu()
                if menu_action == "PLAY": 
                    self.start_level("LEVEL_1")
                elif menu_action == "LEVELS":
                    self.current_game_state = "LEVEL_SELECT_MENU"
                elif menu_action == "QUIT":
                    pygame.quit()
                    sys.exit()

            # ... (sisa dari state machine Anda tetap sama) ...
            elif self.current_game_state == "LEVEL_SELECT_MENU":
                level_choice = self.main_menu.show_levels_menu()
                if level_choice == "BACK":
                    self.current_game_state = "MENU"
                elif level_choice == "TRIAL": 
                    self.start_level("TRIAL")
                elif level_choice == "LEVEL_1":
                    self.start_level("LEVEL_1")
                elif level_choice == "LEVEL_2":
                    self.start_level("LEVEL_2")

            elif self.current_game_state == "PLAYING_LEVEL":
                self.screen.fill("black") 
                if self.active_level_instance:
                    level_status = self.active_level_instance.run()

                    if level_status == "LEVEL_COMPLETE_PROCEED":
                        print(f"{self.current_level_key} complete. Proceeding...")
                        if self.current_level_key == "LEVEL_1":
                            self.start_level("LEVEL_2")
                        else: 
                            print(f"No next level defined after {self.current_level_key}. Returning to menu.")
                            self.active_level_instance = None
                            self.current_game_state = "MENU"
                    
                    elif level_status == "RETURN_TO_MENU":
                        self.active_level_instance = None
                        self.current_game_state = "MENU"
                    
                    elif level_status == "PAUSED": 
                        if not hasattr(self, 'last_game_surface_before_pause'):
                             self.last_game_surface_before_pause = self.screen.copy()
                        self.current_game_state = "PAUSE_MENU"

                else:
                    print("Error: No active level instance while in PLAYING_LEVEL state.")
                    self.current_game_state = "MENU"
            
            elif self.current_game_state == "PAUSE_MENU":
                pause_action = self.main_menu.show_pause_menu(getattr(self, 'last_game_surface_before_pause', None))
                if pause_action == "RESUME":
                    self.current_game_state = "PLAYING_LEVEL"
                elif pause_action == "MENU":
                    self.active_level_instance = None 
                    self.current_game_state = "MENU"
                
                if hasattr(self, 'last_game_surface_before_pause'):
                    del self.last_game_surface_before_pause


            pygame.display.update()
            self.clock.tick(FPS)

if __name__ == '__main__':
    game = Game()
    try:
        game.run()
    finally:
        # --- PERUBAHAN UNTUK DEBUGGING ---
        # Pastikan debugger dan kamera dihentikan dengan benar saat program keluar
        print("\nExiting game...")
        if hasattr(game, 'debugger'):
            game.debugger.stop()
        if hasattr(game, 'camera'):
            game.camera.release()
        pygame.quit()
        sys.exit()