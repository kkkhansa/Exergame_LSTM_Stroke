import pygame, sys
from settings import *
from main_menu import MainMenu
from level.level1 import Level as Level1 # Ubah nama impor untuk kejelasan
# from level.level2 import Level as Level2 # Anda perlu membuat file ini
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
        # Untuk sekarang, kita akan kembali ke menu setelah Level 1
        self.level_definitions = {
            "LEVEL_1": Level1,
            # "LEVEL_2": Level2, # Tambahkan ini setelah Level2 dibuat
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
            print(f"Starting {level_key}")
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
                
                # Input untuk pause bisa ditangani di sini jika state adalah PLAYING_LEVEL
                if self.current_game_state == "PLAYING_LEVEL" and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.active_level_instance:
                            # Minta level untuk masuk ke mode pause dan tampilkan menu pause
                            # Level.toggle_menu() bisa dimodifikasi untuk ini,
                            # atau kita bisa langsung panggil menu pause dari sini.
                            self.current_game_state = "PAUSE_MENU"


            # State machine utama
            if self.current_game_state == "MENU":
                menu_action = self.main_menu.show_main_menu()
                if menu_action == "PLAY": # Tombol PLAY akan memulai Level 1
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
                elif level_choice == "LEVEL_1":
                    self.start_level("LEVEL_1")
                # Tambahkan logika untuk level lain jika ada
                # elif level_choice == "LEVEL_2":
                #     self.start_level("LEVEL_2")


            elif self.current_game_state == "PLAYING_LEVEL":
                self.screen.fill("black") # Latar belakang untuk level
                if self.active_level_instance:
                    level_status = self.active_level_instance.run()

                    if level_status == "LEVEL_COMPLETE_PROCEED":
                        print(f"{self.current_level_key} complete. Proceeding...")
                        # Logika untuk lanjut ke level berikutnya
                        if self.current_level_key == "LEVEL_1":
                            # self.start_level("LEVEL_2") # Jika Level 2 sudah ada
                            print("Level 2 not implemented yet. Returning to menu.")
                            self.active_level_instance = None # Hapus instance level lama
                            self.current_game_state = "MENU" 
                        # Tambahkan logika untuk level lain
                        else:
                            print("All levels complete! Returning to menu.")
                            self.active_level_instance = None
                            self.current_game_state = "MENU"
                    
                    elif level_status == "RETURN_TO_MENU":
                        self.active_level_instance = None
                        self.current_game_state = "MENU"
                    
                    elif level_status == "PAUSED": # Jika Level.run() mengindikasikan pause
                        self.current_game_state = "PAUSE_MENU"
                        # Tidak perlu copy surface di sini karena menu pause akan melakukannya

                    # Jika "RUNNING", tidak ada perubahan state di sini, level terus berjalan
                else:
                    print("Error: No active level instance while in PLAYING_LEVEL state.")
                    self.current_game_state = "MENU"
            
            elif self.current_game_state == "PAUSE_MENU":
                # Tampilkan menu pause. Menu pause akan menangani pembekuan layar.
                # Kita perlu cara untuk mendapatkan surface game terakhir sebelum pause.
                # Untuk sekarang, kita akan membiarkan MainMenu.show_pause_menu()
                # menggambar background default jika tidak ada surface yang dioper.
                # Idealnya, saat K_ESCAPE ditekan di state PLAYING_LEVEL, kita simpan screen.copy().
                
                # Solusi lebih baik: saat K_ESCAPE ditekan di PLAYING_LEVEL,
                # kita ambil screenshot sebelum mengubah state.
                # Ini sudah dilakukan di contoh sebelumnya, kita akan gunakan itu.
                # Untuk sekarang, asumsikan show_pause_menu bisa dipanggil tanpa argumen.
                
                # Jika Anda ingin membekukan layar dari game:
                # 1. Saat K_ESCAPE ditekan di PLAYING_LEVEL, simpan self.screen.copy() ke variabel di Game.
                # 2. Oper variabel itu ke show_pause_menu().
                # Untuk saat ini, kita buat sederhana:
                pause_action = self.main_menu.show_pause_menu(getattr(self, 'last_game_surface_before_pause', None))
                if pause_action == "RESUME":
                    self.current_game_state = "PLAYING_LEVEL"
                elif pause_action == "MENU":
                    self.active_level_instance = None # Hapus instance level saat kembali ke menu
                    self.current_game_state = "MENU"
                # Hapus surface yang disimpan setelah digunakan
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
