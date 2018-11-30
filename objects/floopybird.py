import pygame
import sys
import random
import numpy as np
from itertools import cycle
from pygame.locals import *
from pygame.compat import geterror


class Bird:
    def __init__(self, floor_height, init_pos, grav=1, vel=-9, max_vel=10, flap_acc=-9,
                 max_rotation=-90, angular_velocity=3, feather_off=3):
        # BIRD ATTRIBUTES
        self.x, self.y = init_pos
        self.alive = True
        self.__flap = False

        # PHYSICS VARIABLE
        self.g = grav
        self.v = vel
        self.angle = 20
        self.angular_vel = angular_velocity
        self.flap_acc = flap_acc
        self.max_v = max_vel
        self.max_rotation = max_rotation
        self.feather_off = feather_off

        # LOADING BIRD ASSETS
        self.index = 0
        self.set = (load_image('assets/bird-up.png').convert_alpha(),
                    load_image('assets/bird-mid.png').convert_alpha(),
                    load_image('assets/bird-down.png').convert_alpha())
        self.generator = cycle((1, 2, 1, 0))
        self.floor = floor_height
        self.current = self.set[self.index]

    def update(self, iterator, pipes):
        # FREE FALL OF GRAVITY
        if self.v <= self.max_v and not self.__flap:
            self.v += self.g
        elif self.__flap:  # CHECK FLAPPED
            self.__flap = False
            self.v = self.flap_acc
            self.angle = -self.max_rotation/2
        self.y += self.v

        # GENERATING BIRD IMAGE FROM INDEX
        if iterator % 5 == 0:
            self.index = next(self.generator)
        self.current = self.set[self.index]

        # PIPES COLLISION
        for pipe in pipes:
            if self.__is_collide_with(pipe["UPPER"]) or self.__is_collide_with(pipe["LOWER"])\
                    or self.y >= self.floor:  # IF IT'S SELF.FLOOR-IMAGE_HEIGHT THEN IT WOULD STOP PREMATURELY
                self.alive = False

        # ANGULAR ROTATION ( BASED DEGREES )
        if self.angle > self.max_rotation:
            self.angle += -self.angular_vel

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.current, self.angle)
        screen.blit(rotated, (self.x, self.y))

    def flap(self):
        self.__flap = True

    def __is_collide_with(self, image):
        # CREATING A RECT FOR BIRD AND SUBTRACTING FEATHER OFFSETS ( AVOID STRICT COLLISION )
        rect = pygame.Rect((self.x+self.feather_off, self.y+self.feather_off),
                           np.array(self.current.get_size()) - self.feather_off * 2)
        return rect.colliderect(image.get_rect())  # BUILT IN FUNCTION TO CHECK RECTANGULAR COLLISION


class Pipe:
    # POSITION STANDS FOR (X, Y) OF THE TOP LEFT COORDINATE OF THE PIPE
    def __init__(self, position, dimension):
        self.dimension = dimension
        self.position = np.array(position)

    def set_position(self, position):
        self.position = np.array(position)

    def move(self, velocity):
        self.position[0] += velocity

    def getx(self):
        return self.position[0]

    def setx(self, x):
        self.position[0] = x

    def getw(self):
        return self.dimension[0]

    def geth(self):
        return self.dimension[1]

    def get_rect(self):
        return pygame.Rect(self.position, self.dimension)


class Pipes:
    def __init__(self, base_off, pipe_gap=100, quantity=2, windowwidth=288,
                 windowheight=512, boundary=50, velocity=-4):
        # LOADING IN PIPE ASSETS AND INITIALIZING ALL SORTS OF DIMENSIONS
        self.assets = {
            "PIPE-UPPER": load_image('assets/pipe-upper.png').convert_alpha(),
            "PIPE-LOWER": load_image('assets/pipe-lower.png').convert_alpha(),
        }
        self.dimension = self.assets["PIPE-UPPER"].get_size()
        self.screen = [windowwidth, windowheight]
        self.screen[1] *= base_off

        # PIPES ATTRIBUTE VARIABLES
        self.pipe_gap = pipe_gap
        self.boundary = boundary  # REPRESENTS THE UPPER LIMIT FOR A PIPE
        self.quantity = quantity
        self.interval = ((windowwidth + self.dimension[0]) / quantity) - self.dimension[0]
        self.velocity = velocity

        # PIPE INTIALIZATION
        self.pipes = []
        for x in range(quantity):
            uppipe, downpipe = self.__get_new_pipes(x)
            self.pipes.append({
                "UPPER": uppipe,
                "LOWER": downpipe
            })

    def update(self):
        for pipe in self.pipes:
            pipe["UPPER"].move(self.velocity)
            pipe["LOWER"].move(self.velocity)
            if pipe["UPPER"].getx() < -self.dimension[0]:  # BOTH PIPES MOVE SIMULTANEOUSLY
                pipe["UPPER"], pipe["LOWER"] = self.__get_new_pipes()

    def draw(self, screen):
        for pipe in self.pipes:
            if pipe["UPPER"].position[0] <= self.screen[0]:
                screen.blit(self.assets["PIPE-UPPER"], pipe["UPPER"].position)
                screen.blit(self.assets["PIPE-LOWER"], pipe["LOWER"].position)

    # GENERATES A PAIR OF PIPES BASED OFF OF 'PIPE ATTRIBUTES'
    def __get_new_pipes(self, x=0):
        uppipe = Pipe(position=(
            x * (self.dimension[0] + self.interval) + self.screen[0],
            random.randint(self.boundary, int((self.screen[1] + self.pipe_gap)/2)) - self.dimension[1]),
            dimension=self.dimension)
        downpipe = Pipe(position=(uppipe.position[0], uppipe.position[1] + self.dimension[1] + self.pipe_gap),
                        dimension=self.dimension)
        return uppipe, downpipe


class Game:
    def __init__(self, windowwidth=288, windowheight=512, caption='TITLE',
                 init_pos=(50, 256), base_speed=2, base_off=0.8):
        pygame.init()

        # SCREEN SETUP
        self.resolution = (windowwidth, windowheight)
        self.SCREEN = pygame.display.set_mode(self.resolution)
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

        # ASSETS-LOADING
        self.assets = {
            "BACKGROUND": load_image('assets/bg.png').convert(),
            "BASE": load_image('assets/base.png').convert()
        }

        # OBJECTS INITIALIZATION
        self.bird = Bird(init_pos=init_pos, floor_height=self.resolution[1]*base_off)
        self.bird_index = 0
        self.pipes = Pipes(base_off)
        self.base_x1, self.base_x2, self.base_y = (0, windowwidth, windowheight*0.9)
        self.base_speed = base_speed

    def main(self):
        loop_iterator = 0
        running = True
        while running:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN and event.key == K_SPACE:
                    self.bird.flap()

            # UPDATING OBJECTS ( RUNS ONLY IF BIRD IS ALIVE )
            if self.bird.alive:
                self.bird.update(loop_iterator, self.pipes.pipes)
                self.pipes.update()
                self.base_x1 -= self.base_speed
                self.base_x2 -= self.base_speed
                if self.base_x1 <= -self.resolution[0]:
                    self.base_x1 = self.resolution[0]
                if self.base_x2 <= -self.resolution[0]:
                    self.base_x2 = self.resolution[0]
                loop_iterator = (loop_iterator + 1) % 30

            # DRAWING ONTO SCREEN
            self.SCREEN.blit(self.assets["BACKGROUND"], (0, 0))
            self.bird.draw(self.SCREEN)
            self.pipes.draw(self.SCREEN)
            self.SCREEN.blit(self.assets["BASE"], (self.base_x1, self.base_y))
            self.SCREEN.blit(self.assets["BASE"], (self.base_x2, self.base_y))

            pygame.display.update()


def load_image(file_path):
    try:
        image = pygame.image.load(file_path)
    except pygame.error:
        raise SystemExit(str(geterror()))
    return image
