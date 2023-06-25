#! /usr/bin/python3
import pygame
import pygame_menu
import random
import os
import numpy as np
import time

import easygui
import sqlite3
import database

GOD_MODE = False
MAX_NUMB_BULL=5

REDIS_ENABLED = False # Set to True in order to enable redis connection and voice command control

if REDIS_ENABLED:
    import redis

class Player(pygame.sprite.Sprite):
   def __init__(self, pos, image_file, health = 5, score = 0, movement_speed = 10, voice_movement_speed= 100):
        super().__init__()
        
        self.size = 80
        self.health = health
        self.score = score

        self.image = pygame.transform.scale(pygame.image.load(os.path.join('data', image_file)), (self.size, self.size))
        
        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]

        self.movement_speed = movement_speed
        self.voice_movement_speed = voice_movement_speed

        self.min_shoot_interval = 0.1
        self.last_bullet_time = 0

        self.bul_list=[]
        
   def control(self):
        if REDIS_ENABLED:
            rd = redis.Redis(host="localhost")
            if rd.get("go_dir") is not None:
                dir = rd.get("go_dir").decode()
                if dir == "left" and self.rect.x > 0:
                    self.rect.x -= self.voice_movement_speed
                if dir == "right" and self.rect.x < game.width - self.size:
                    self.rect.x += self.voice_movement_speed
                if dir == "up" and self.rect.y > 0:
                    self.rect.y -= self.voice_movement_speed
                if dir == "down" and self.rect.y < game.height - self.size:
                    self.rect.y += self.voice_movement_speed

                rd.delete("go_dir")
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.x > 0:
            self.rect.x -= self.movement_speed
        if keys[pygame.K_RIGHT] and self.rect.x < game.width - self.size:
            self.rect.x += self.movement_speed
        if keys[pygame.K_UP] and self.rect.y > 0:
            self.rect.y -= self.movement_speed
        if keys[pygame.K_DOWN] and self.rect.y < game.height - self.size:
            self.rect.y += self.movement_speed
        if keys[pygame.K_SPACE]:
            if time.time() - self.last_bullet_time > self.min_shoot_interval and len(self.bul_list) < MAX_NUMB_BULL:
                new_bullet=Bullet((self.rect.x,self.rect.y),'bullet.png')
                game.all_sprites_list.add(new_bullet)
                self.bul_list.append(new_bullet)

                self.last_bullet_time = time.time()

        i = 0
        while i < len(self.bul_list):
            if not self.bul_list[i].active:
                del self.bul_list[i]
            else:
                i += 1
            


class Bullet(pygame.sprite.Sprite):
   def __init__(self, pos, image_file, speed = -5, size = 28):
        super().__init__()
        
        self.size = size
        self.image = pygame.transform.scale(pygame.image.load(os.path.join('data', image_file)), (self.size, self.size))
        self.image = pygame.transform.rotate(self.image, -90)
        
        self.rect = self.image.get_rect()

        self.pos = pos
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.speed = speed

        self.active = True

   def update(self):        
        self.rect.y += self.speed

        if self.rect.y < 0:
            self.active = False


class Enemy(pygame.sprite.Sprite):
   def __init__(self, pos, image_file, speed = 5, size = 80):
        super().__init__()
        
        self.size = size
        self.image = pygame.transform.scale(pygame.image.load(os.path.join('data', image_file)), (self.size, self.size))
        self.image = pygame.transform.rotate(self.image, 180)
        
        self.rect = self.image.get_rect()

        self.pos = pos
        self.rect.x = pos[0]
        self.rect.y = pos[1]
        self.speed = speed

        self.active = True

   def update(self):        
        self.rect.y += self.speed

        if self.rect.y > game.height:
            self.active = False





class Game():
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.enemies : list[Enemy] = []
        self.all_sprites_list = pygame.sprite.Group()
        
        size = (self.width, self.height)
        self.screen = pygame.display.set_mode(size)
        

        self.player = Player((self.width/2, self.height - 100), "plane.png")
        self.all_sprites_list.add(self.player)


        self.bg = bg = pygame.image.load("data/bg.jpg")


        self.initial_max_num_of_enemies = 10
        self.max_num_of_enemies = 10
        self.initial_enemy_spawn_chance = 0.1
        self.enemy_spawn_chance = 0.1
        self.initial_enemies_speed = 5
        self.enemies_speed = 5

        self.init_time = time.time()

        self.state = 0 # 0 -> game running; 1 -> game over


    def update_difficulty(self):
        t = int(time.time() - self.init_time)

        self.enemy_spawn_chance = min(self.initial_enemy_spawn_chance + 0.1 * (t / 1), 1)
        self.max_num_of_enemies = self.initial_max_num_of_enemies + (t / 1)

        self.enemies_speed = self.initial_enemies_speed + (t / 5)

    def show_game_over_screen(self):
        survived_time = int(time.time() - self.init_time)
        name = easygui.enterbox("Enter your name", "Game Over")


        rank = database.insert_new_record(name, survived_time)

        game_over_screen_fade = pygame.Surface((self.width, self.height))
        game_over_screen_fade.fill((0, 0, 0))
        game_over_screen_fade.set_alpha(160)
        self.screen.blit(game_over_screen_fade, (0, 0))

        font = pygame.font.SysFont('arial', 62)
        text = font.render("Game Over!", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (self.width / 2, self.height / 2)

        self.screen.blit(text, textRect)

        mins = survived_time // 60
        secs = survived_time % 60

        min_text = "minute"
        if mins != 1:
            min_text += 's'

        sec_text = "second"
        if secs != 1:
            sec_text += 's'
        
        font = pygame.font.SysFont('arial', 32)
        text = font.render(f"{name} survived {mins} {min_text} {secs} {sec_text}!", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (self.width / 2, self.height / 2 + 80)

        self.screen.blit(text, textRect)


        font = pygame.font.SysFont('arial', 22)

        text = font.render(f"{name}'s rank: {rank}", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (self.width / 2, self.height / 2 + 150)

        self.screen.blit(text, textRect)
        
        text = font.render("Press ENTER to restart", True, (255, 255, 255))
        textRect = text.get_rect()
        textRect.center = (self.width / 2, self.height / 2 + 200)

        self.screen.blit(text, textRect)
    
    def run(self):
        exit = True
        clock = pygame.time.Clock()
        
        while exit:
            for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit = False
            
            if self.state == 0:
                self.all_sprites_list.update()
                self.screen.fill((255, 255, 255))
                self.screen.blit(self.bg, (0, 0))

                self.all_sprites_list.draw(self.screen)

                self.player.control()


                # Removing deactive enemies and checking for collisions
                i = 0
                while i < len(self.enemies):
                    if not self.enemies[i].active:
                        self.all_sprites_list.remove(self.enemies[i])
                        del self.enemies[i]
                    else:
                        if pygame.sprite.collide_mask(self.player, self.enemies[i]) and not GOD_MODE:
                            # print("collided")
                            self.player.health -= 1
                            self.all_sprites_list.remove(self.enemies[i])
                            del self.enemies[i]

                            if self.player.health == 0:
                                self.state = 1
                                self.show_game_over_screen()
                        j = 0
                        for b in self.player.bul_list:
                            
                            if pygame.sprite.collide_mask(b, self.enemies[i]):
                                self.all_sprites_list.remove(self.enemies[i])
                                self.all_sprites_list.remove(b)
                                del self.enemies[i]
                                del self.player.bul_list[j]
                                
                                break
                            j += 1


                        else:
                            i += 1

                    
                    if i >= len(self.enemies):
                        break
                
                
                
                # Spawn new enemies
                if len(self.enemies) < self.max_num_of_enemies:
                    if random.random() < self.enemy_spawn_chance:
                        position = (random.randint(0, game.width - 80), 0)

                        # calculating minimum distance of new enemy to all enemies to avoid spawning on another enemy
                        min_dis = game.width
                        for x in self.enemies:
                            dis = np.linalg.norm(np.array(x.pos) - np.array(position))
                            if dis < min_dis:
                                min_dis = dis
                        
                        if min_dis > 100:
                            new_enemy = Enemy(position, 'enemy.png', speed=self.enemies_speed)
                            self.enemies.append(new_enemy)
                            self.all_sprites_list.add(new_enemy)

                self.update_difficulty()


                font = pygame.font.SysFont('arial', 42)
                text = font.render('♥' * self.player.health, True, (255, 0, 0))
                textRect = text.get_rect()
                textRect.topleft = (10, 10)

                self.screen.blit(text, textRect)
            
            elif self.state == 1:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_RETURN]:
                    self.state = 0
                    self.player.health = 5
                    self.all_sprites_list.empty()
                    self.all_sprites_list.add(self.player)
                    self.enemies = []
                    self.init_time = time.time()

                    self.enemy_spawn_chance = self.initial_enemy_spawn_chance
                    self.max_num_of_enemies = self.initial_max_num_of_enemies
                    self.enemies_speed = self.initial_enemies_speed


            pygame.display.flip()
            clock.tick(60)




def start():
    global game
    game = Game(800, 800)
    game.run()

    pygame.quit()


def loadMenu():
    surface = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("DodgeLane")
    theme = pygame_menu.themes.THEME_DARK
    theme.widget_font=pygame_menu.font.FONT_8BIT
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_SIMPLE

    menu = pygame_menu.Menu('DodgeLane', 800, 800, theme=theme)
    menu.add.button("Play", start)
    menu.add.button("Exit",pygame_menu.events.EXIT)
    menu.mainloop(surface)


if __name__ == '__main__':
    pygame.init()
    pygame.font.init()

    loadMenu()
