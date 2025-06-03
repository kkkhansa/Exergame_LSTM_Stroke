import pygame, sys
from settings import *
from main_menu import MainMenu
from level.level1 import Level as Level1 # Ubah nama impor untuk kejelasan
from level.level2 import Level as Level2 # Anda perlu membuat file ini dan memastikan impor ini benar
from level.trial import TrialLevel # TrialLevel untuk level percobaan, jika ada
from camera import HandGestureCamera
# from ui import UI # UI dikelola di dalam Level

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Heart Collector') # Ganti judul game jika mau
        self.clock = pygame.time.Clock()
        
        self.current_game_state = "MENU" # Menggunakan nama state yang lebih deskriptif
        self.active_level_instance = None # Untuk menyimpan instance level yang sedang berjalan

        self.camera = HandGestureCamera()
        self.main_menu = MainMenu(self.screen) # MainMenu juga akan berfungsi sebagai font_renderer

        # Placeholder untuk Level 2 - Anda perlu membuat kelas Level2
        self.level_definitions = {
            "TRIAL": TrialLevel, # Level percobaan, jika ada
            "LEVEL_1": Level1,
            "LEVEL_2": Level2, # Tambahkan ini setelah Level2 dibuat dan diimpor
        }
        self.current_level_key = None


    def start_level(self, level_key):
        if level_key in self.level_definitions:
            self.current_level_key = level_key
            # Oper screen dan main_menu (sebagai font_renderer) ke Level
            self.active_level_instance = self.level_definitions[level_key](
                camera_instance=self.camera,
                screen_surface=self.screen,
                font_renderer=self.main_menu # MainMenu memiliki metode get_font
            )
            self.current_game_state = "PLAYING_LEVEL"
            print(f"Starting {level_key}") # Pesan ini akan muncul jika level_key ada di definisi
        else:
            print(f"Error: Level key '{level_key}' not found in definitions.")
            self.current_game_state = "MENU" # Kembali ke menu jika level tidak ditemukan

    def run(self):
        while True:
            # Event handling umum (bisa dipindahkan ke fungsi terpisah jika kompleks)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.camera: self.camera.release()
                    pygame.quit()
                    sys.exit()
                
                if self.current_game_state == "PLAYING_LEVEL" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.active_level_instance:
                            # Simpan layar saat ini sebelum masuk ke menu pause
                            self.last_game_surface_before_pause = self.screen.copy()
                            self.current_game_state = "PAUSE_MENU"


            # State machine utama
            if self.current_game_state == "MENU":
                menu_action = self.main_menu.show_main_menu()
                if menu_action == "PLAY": 
                    self.start_level("LEVEL_1")
                elif menu_action == "LEVELS":
                    self.current_game_state = "LEVEL_SELECT_MENU"
                elif menu_action == "QUIT":
                    if self.camera: self.camera.release()
                    pygame.quit()
                    sys.exit()

            elif self.current_game_state == "LEVEL_SELECT_MENU":
                level_choice = self.main_menu.show_levels_menu()
                if level_choice == "BACK":
                    self.current_game_state = "MENU"
                elif level_choice == "TRIAL": # Tambahkan opsi untuk memulai Level Percobaan
                    self.start_level("TRIAL")
                elif level_choice == "LEVEL_1":
                    self.start_level("LEVEL_1")
                elif level_choice == "LEVEL_2": # Tambahkan opsi untuk memulai Level 2 dari menu level
                    self.start_level("LEVEL_2")


            elif self.current_game_state == "PLAYING_LEVEL":
                self.screen.fill("black") 
                if self.active_level_instance:
                    level_status = self.active_level_instance.run()

                    if level_status == "LEVEL_COMPLETE_PROCEED":
                        print(f"{self.current_level_key} complete. Proceeding...")
                        if self.current_level_key == "LEVEL_1":
                            self.start_level("LEVEL_2") # Aktifkan pemanggilan untuk memulai Level 2
                        # Tambahkan logika untuk level lain jika ada, misal setelah Level 2
                        # elif self.current_level_key == "LEVEL_2":
                        #     print("Level 2 complete! Congratulations!")
                        #     self.active_level_instance = None 
                        #     self.current_game_state = "MENU" 
                        else: # Jika tidak ada level berikutnya yang didefinisikan setelah level saat ini
                            print(f"No next level defined after {self.current_level_key}. Returning to menu.")
                            self.active_level_instance = None
                            self.current_game_state = "MENU"
                    
                    elif level_status == "RETURN_TO_MENU":
                        self.active_level_instance = None
                        self.current_game_state = "MENU"
                    
                    elif level_status == "PAUSED": 
                        # Simpan layar saat ini jika status PAUSED dikembalikan oleh level
                        # (Meskipun lebih umum K_ESCAPE ditangani di loop utama Game)
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
        if hasattr(game, 'camera') and game.camera:
            game.camera.release()
