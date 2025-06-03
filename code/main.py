import pygame, sys
from settings import *
from main_menu import MainMenu
# from level.trial_level import TrialLevel
from level.level1 import Level
# from level.level2 import Level2
from camera import HandGestureCamera

#debugging
#from level.test_level import Level



class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('My Game')
        self.clock = pygame.time.Clock()
        self.state = "MENU" # CHANGE TO "MENU" TO START AT MAIN MENU
        self.paused_surface = None  # Store frozen screen
        self.camera = HandGestureCamera()  # Initialize the camera

        self.menu = MainMenu(self.screen)
        self.level = None

    def run(self):
        while True:
            if self.state == "MENU":
                result = self.menu.show_main_menu()
                if result == "PLAY":
                    self.level = Level(self.camera)
                    self.state = "PLAY"
                elif result == "LEVELS":
                    self.state = "LEVELS"
                elif result == "QUIT":
                    self.camera.cap.release()  # Release the camera
                    pygame.quit()
                    sys.exit()

            elif self.state == "PLAY":
                self.screen.fill("black")  # Clear the screen for the level
                self.level.run()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.camera.cap.release()
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        # Freeze the current screen
                        self.paused_surface = self.screen.copy()
                        result = self.menu.show_pause_menu(self.paused_surface)
                        if result == "MENU":
                            self.state = "MENU"
                        elif result == "RESUME":
                            self.state = "PLAY"

            elif self.state == "LEVELS":
                self.screen.fill("black")  # Clear the screen for levels menu
                result = self.menu.show_levels_menu()
                if result == "BACK":
                    self.state = "MENU"
                elif result == "TRIAL" :
                    # self.level = TrialLevel(self.screen)
                    pass  # Placeholder for trial level logic
                elif result == "LEVEL_1":
                    # Placeholder for level selection logic
                    self.level = Level(self.camera)
                    self.state = "PLAY"
                elif result == "LEVEL_2":
                    # self.level = Level2(self.screen)
                    pass # Placeholder for level selection logic
                    #self.level = Level1(self.screen)
               
            pygame.display.update()
            self.clock.tick(FPS)

if __name__ == '__main__':
    game = Game()
    try:
        game.run()
    finally:
        # Pastikan kamera dirilis meskipun ada error yang tidak tertangkap di run()
        if hasattr(game, 'camera') and game.camera:
            game.camera.release()
