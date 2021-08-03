import time
import pygame
from pygame.locals import *
import numpy as np
from matplotlib import pyplot as plt
import random
from PIL import Image
import copy

#start pygame
pygame.init()

#set window size
screen_width = 1400
screen_height = 800

#set clock for fps
clock = pygame.time.Clock()
fps = 60

#initialize window
screen = pygame.display.set_mode((screen_width,screen_height))
pygame.display.set_caption('Platformer')

#load images
bg_img = pygame.image.load('background_pixel.png')

#tile size for grid
tile_size = 50

#scaling from number of tiles to number of pixels
#assume we have square screen
scaling = screen_height / tile_size

#player sprite dimensions
player_height = 2*tile_size
player_width = 1*tile_size

#draw game grid
def draw_grid():
    for line in range(0,int(screen_width/tile_size)):
        pygame.draw.line(screen, (255,255,255), (0, line * tile_size), (screen_width, line * tile_size))
        pygame.draw.line(screen, (255,255,255), (line * tile_size, 0), (line * tile_size, screen_width))

#import player walking gif
def split_animated_gif(gif_file_path):
    ret = []
    gif = Image.open(gif_file_path)
    for frame_index in range(gif.n_frames):
        gif.seek(frame_index)
        frame_rgba = gif.convert("RGBA")
        pygame_image = pygame.image.fromstring(
            frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode
        )
        ret.append(pygame_image)
    return ret

walking_right_gif = split_animated_gif('walking.gif')
walking_left_gif = split_animated_gif('walking_left.gif')

#define the player class
class Player():
    def __init__(self, x, y):
        #initialize player sprite and coordinates
        img_right = pygame.image.load('walking.gif')
        img_left = pygame.image.load('walking_left.gif')
        self.index_right = 0
        self.index_left = 0
        self.counter_right = 0
        self.counter_left = 0
        self.anim_right = []
        self.anim_left = []
        self.is_anim_right = False
        self.is_anim_left = False
        #load walking animation for walking right
        for img in walking_right_gif:
            img = pygame.transform.scale(img,(player_width,player_height))
            #append image 3 times to slow down animation
            self.anim_right += [img] * 3
        #load walking animation for walking left
        for img in walking_left_gif:
            img = pygame.transform.scale(img,(player_width,player_height))
            #append image 3 times to slow down animation
            self.anim_left += [img] * 3
        self.image = self.anim_right[self.index_right]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jump_acceleration = int(0.9*tile_size)
        self.is_jump = False
        self.walk_speed = int(tile_size/5)
    
    def update(self):     
    
        #get keypress
        key = pygame.key.get_pressed()
        dx = 0
        dy = 0

        #check for horizontal movement. If so, animate.
        #default is NO animation
        self.is_anim_right = False        
        self.is_anim_left = False
        if key[pygame.K_LEFT]:
            dx-=self.walk_speed
            self.is_anim_left = True
        elif key[pygame.K_RIGHT]:
            self.is_anim_right = True
            dx+=self.walk_speed
        
        #special event handling so that player does not hold down jump 
        if key[pygame.K_SPACE]:
            #no double jumping
            if self.is_jump == False:
                self.vel_y -= self.jump_acceleration
                self.is_jump = True
    
        #set terminal velocity equal to initial jump acceleration 
        if self.vel_y < (self.jump_acceleration):
            self.vel_y += int(self.jump_acceleration/10)
 
        #set downwards displacement from velocity
        dy = self.vel_y        

        #collision checking
        for tile in world.tile_list:
            #check for y-dir collision
            #tile has format tile(picture,rectangle object)
            #pass a rectangle object representing where the character wants to 
            #go to implement pre-emptive collision checking
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                #check if jumping, i.e below block and hitting roof
                if self.vel_y < 0:
                    #touch top of sprite to roof
                    dy = tile[1].bottom - self.rect.top
                #else we are landing on a block
                elif self.vel_y >= 0:
                    dy = tile[1].top - self.rect.bottom
                    #we have landed back on a block, set is_jump to be false.
                    self.is_jump = False
                self.vel_y = 0
            elif tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0

        #update co-ordinates
        self.rect.x += dx
        self.rect.y += dy
 
        #update animation if we are walking right
        if self.is_anim_right:
            self.index_right += 1
            self.image = self.anim_right[self.index_right % len(self.anim_right)]

        #update animation if we are walking left
        if self.is_anim_left:
            self.index_left += 1
            self.image = self.anim_left[self.index_left % len(self.anim_left)]
 

        #check we are not leaving the map
        if self.rect.bottom > screen_height:
            self.rect.bottom = screen_height
            dy=0
            self.is_jump = False
        elif self.rect.top < 0: 
            self.rect.top = 0
            dy=0
        if (self.rect.x + self.rect.width) > screen_width:
            #generate fresh world
            self.rect.x = 0
            world.scroll()
            dx = 0
        if (self.rect.x < 0):
            self.rect.x = 0
            dx = 0
           
        #draw sprite
        screen.blit(self.image,self.rect)

#define the world, i.e where we have platorms
class World():
    
    def __init__(self):
        #initialize our world

        #procedurally generate level
        [self.height,self.width] = [int(screen_height/tile_size),int(screen_width/tile_size)]
        self.data = np.zeros([self.height,self.width])

        #gravel layer on bottom
        self.data[-1,:] = 1
        #dirt layer on top of this
        self.data[-2,:] = 2
        #grass layer on top of this
        self.data[-3,:] = 3

        self.tile_list_base = []
        self.tile_list_random = []
        self.tile_list = []

        #load images

        [self.grid_height, self.grid_width] = np.shape(self.data)

        #load block images
        gravel_block = pygame.image.load('gravel.jpg')
        dirt_block = pygame.image.load('dirt.jpg')
        grass_block = pygame.image.load('grass.jpg')
        #iterate over grid rows
        for i in range(self.grid_height):
            #iterate over grid cols
            for j in range(self.grid_width):
                if self.data[i][j] == 1:
                    #draw a gravel block to the screen
                    img = pygame.transform.scale(gravel_block, (tile_size,tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = j * tile_size
                    img_rect.y = i * tile_size
                    tile = (img, img_rect)
                    self.tile_list_base.append(tile)
                elif self.data[i][j] == 2:
                    #draw a dirt block to the screen
                    img = pygame.transform.scale(dirt_block, (tile_size,tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = j * tile_size
                    img_rect.y = i * tile_size
                    tile = (img, img_rect)
                    self.tile_list_base.append(tile)
                elif self.data[i][j] == 3:
                    #draw a grass block to the screen
                    img = pygame.transform.scale(grass_block, (tile_size,tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = j * tile_size
                    img_rect.y = i * tile_size
                    tile = (img, img_rect)
                    self.tile_list_base.append(tile)
                elif self.data[i][j] == 4:
                    #draw an enemy to the screen
                    enemy = Enemy(j*tile_size, i*tile_size)
                    enemy_group.add(enemy)

        #generate blocks randomly
        self.generate_random_blocks()
        self.tile_list = np.concatenate([self.tile_list_base,self.tile_list_random])

    def draw(self):
        #draw the loaded blocks to the screen
        for tile in self.tile_list:
            #format of tile is:
            #tile = [image, coordinates]
            screen.blit(tile[0],tile[1])

    def generate_random_blocks(self):
        #procedurally generate solo dirt blocks
        print("generate_random_blocks")
        block_img = pygame.image.load('gravel.jpg')
        for i in range(self.grid_height):
            for j in range(self.grid_width):
                if random.uniform(0,1) > 0.95:
                    #draw a gravel block to the screen
                    img = pygame.transform.scale(block_img, (tile_size,tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = j * tile_size
                    img_rect.y = i * tile_size
                    tile = (img, img_rect)
                    self.tile_list_random.append(tile)

    def scroll(self):
        #refresh random blocks
        self.tile_list_random = []
        self.generate_random_blocks()
        self.tile_list = np.concatenate([self.tile_list_base,self.tile_list_random])

#enemy class, moves around and jumps randomly
class Enemy(pygame.sprite.Sprite):
    
    def __init__(self,x,y):
        pygame.sprite.Sprite.__init__(self)
        image = pygame.image.load('enemy.png')
        self.image = pygame.transform.scale(image, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

#make enemy group
enemy_group = pygame.sprite.Group()
#initialize world object
world = World()
#initialize player object
player = Player(100,5*tile_size-player_height)

#start game logic loop
run = True
while run == True:
    #set fps
    clock.tick(fps)

    #draw screen
    screen.blit(bg_img, (0,0))

    #draw blocks
    world.draw()

    #draw enemies
    enemy_group.draw(screen)

    #draw grid
    #draw_grid()

    #draw player to screen
    player.update()

    #process events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

#exit game
pygame.quit()
