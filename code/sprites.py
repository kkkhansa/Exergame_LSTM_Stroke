import pygame
from settings import *
from random import choice

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, groups, sprite_type, surface=None):
        super().__init__(groups)
        self.sprite_type = sprite_type
        
        if surface:
            self.image = surface
        else:
            self.image = pygame.Surface((TILESIZE, TILESIZE))
            if sprite_type == 'invisible':
                self.image.set_alpha(0)
            elif sprite_type == 'grass':
                self.image.fill((100, 200, 100))
            elif sprite_type == 'object':
                self.image.fill((139, 69, 19))
        
        self.rect = self.image.get_rect(topleft=pos)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacle_sprites):
        super().__init__(groups)
        self.image = pygame.Surface((32, 48))
        self.image = pygame.image.load("graphics/test/player.png").convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(-6, HITBOX_OFFSET['player'])
        
        
        # Movement
        self.direction = pygame.math.Vector2()
        self.speed = 5
        self.obstacle_sprites = obstacle_sprites
        
        # Inventory
        self.inventory = {'heart': 0} # add inventory to the player class

    def input(self):
        keys = pygame.key.get_pressed()
        
        # Movement input
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0
            
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
        else:
            self.direction.x = 0

    def move(self, speed):
        if self.direction.magnitude() != 0:
            self.direction = self.direction.normalize()
        
        self.rect.x += self.direction.x * speed
        self.collision('horizontal')
        self.rect.y += self.direction.y * speed
        self.collision('vertical')

    def collision(self, direction):
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.x > 0:  # moving right
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0:  # moving left
                        self.rect.left = sprite.rect.right

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.direction.y > 0:  # moving down
                        self.rect.bottom = sprite.rect.top
                    if self.direction.y < 0:  # moving up
                        self.rect.top = sprite.rect.bottom

    def add_item(self, item_type):
        """Add item to inventory"""
        if item_type in self.inventory:
            self.inventory[item_type] += 1
        else:
            self.inventory[item_type] = 1

    def update(self):
        self.input()
        self.move(self.speed)

class Item(pygame.sprite.Sprite):
    def __init__(self, pos, groups, item_type):
        super().__init__(groups)
        self.item_type = item_type
        
        # Create item visuals based on type
        self.image = pygame.Surface((24, 24))
        if item_type == 'coin':
            self.image.fill((255, 215, 0))  # Gold
        elif item_type == 'key':
            self.image.fill((192, 192, 192))  # Silver
        elif item_type == 'potion':
            self.image.fill((255, 0, 255))  # Magenta
        
        self.rect = self.image.get_rect(center=pos)
        
        # Animation
        self.float_timer = 0
        self.original_y = pos[1]

    def update(self):
        # Floating animation
        self.float_timer += 0.1
        self.rect.y = self.original_y + pygame.math.Vector2(0, 5).rotate(self.float_timer * 10).y

