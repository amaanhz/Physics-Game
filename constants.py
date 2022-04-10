import pygame, math, os

DEBUG = False
DEBUG_LEVEL = 1

WHITE = (255, 255, 255)
RED = (255, 0, 0)
PINK = (204, 33, 64)
GREEN = (28, 214, 59)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
ORANGE = (247, 160, 20)
GREY = (119, 119, 119)
NEARLYBLACK = (61, 61, 61)
MAGENTA = (181, 49, 201)
STEEL = (159, 161, 163)
BACKGROUNDCOLOUR = (16, 15, 15)

OPTIMUS = os.path.join("assets", "fonts", "Optimus.otf")
OPTIMUS_BOLD = os.path.join("assets", "fonts", "Optimus_Bold.otf")
FUTURE_LIGHT = os.path.join("assets", "fonts", "Future_Light.ttf")
UNISPACE = os.path.join("assets", "fonts", "unispace_rg.ttf")
QUINGER = os.path.join("assets", "fonts", "Quinger.ttf")
QUALY = os.path.join("assets", "fonts", "Qualy Bold.ttf")
EXO = os.path.join("assets", "fonts", "Exo2-Regular.otf")

WINDOW_SIZE = (1600, 900)
WINDOW_CENTRE = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
swidth, sheight = WINDOW_SIZE
FPS = 200

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)

player_image = pygame.image.load("assets/sprites/character.png").convert_alpha()
ball_image = pygame.image.load("assets/sprites/ball.png").convert_alpha()
ball_image_white = pygame.image.load("assets/sprites/ball_white.png").convert_alpha()
ball_image_orange = pygame.image.load("assets/sprites/ball_orange.png").convert_alpha()

RAD = math.pi / 180

GRAVITYON = True
GRAVITY = 15
AIR_DENSITY = 1.2041
PLAYER_DRAG_COEFFICIENT = 1.15
SPHERE_DRAG_COEFFICIENT = 0.5
PLAYER_ROTATION_SPEED = 75

AIRSTREAM_PARTICLENUM = 50

METRE = player_image.get_height() * (1 / 1.7)

SCOREBASE = 10000
HITPENALTY = 500

MAXUSERNAMECHARS = 15

OPTIMALS = {
    "1": 15,
    "2": 20
}