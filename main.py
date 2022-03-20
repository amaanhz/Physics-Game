from physics import *
from constants import *
import os, csv

largeBoldMenu = pygame.font.Font(FUTURE_LIGHT, 100)
mediumMenu = pygame.font.Font(OPTIMUS, 28)

def getCameraTrack(pos, lpos, lwidth, lheight):
    """
    :param pos: The position of the player
    :type pos: Vec2
    :param lpos: The position of the level background
    :type lpos: Vec2
    :param lwidth: The width of the level
    :type lwidth: int
    :param lheight: The height of the level
    :type lheight: int
    :return: The new level position required to move the "camera" accordingly with the player.
    """
    x, y = pos.x, pos.y
    swidth, sheight = WINDOW_SIZE # Screen width and height
    halfw, halfh = swidth / 2, sheight / 2
    maxWidthOffset = lwidth - swidth # The maximum width and height the level can move before the image ends
    maxHeightOffset = lheight - sheight
    newlpos = list(lpos) # New level position will be calculated and stored in a list

    if x + halfw > swidth and lpos[0] > -maxWidthOffset:
        difference = x + halfw - swidth
        newlpos[0] = lpos[0] - difference
    elif x - halfw < 0 and lpos[0] < 0:
        difference = abs(x - halfw)
        newlpos[0] = lpos[0] + difference

    if y - halfh < 0 and lpos[1] > -maxHeightOffset:
        difference = y - halfh
        newlpos[1] = lpos[1] + difference
    elif y + halfh > sheight and lpos[1] < 0:
        difference = y + halfh - sheight
        newlpos[1] = lpos[1] + difference
    return [round(a) for a in newlpos]

def level_load(level):
    ## All level info stored as a dictionary
    info = {
        "background": os.path.join("levels", level, "background.png"),
        "world": [],
        "objects": [],
        "objectives": [],
        "player": None
    }

    ## LOADING WORLD COLLIDERS ##
    with open(os.path.join("levels", level, "world.csv"), "r") as file:
        reader = csv.reader(file)
        for row in reader:
            objInfo = list(map(int, row)) # Convert all coordinate values for the rect into integers
            info["world"] = info["world"] + [WorldCollider(pygame.Rect(objInfo[0], objInfo[1], objInfo[2], objInfo[3]))]

    ## LOADING PHYSICS OBJECTS (Regular) ##
    with open(os.path.join("levels", level, "objects.csv"), "r") as file:
        reader = csv.reader(file)
        for i, row in enumerate(reader):
            pos = tuple(map(int, row[0:2]))
            physInfo = list(map(float, row[3:5])) + [float(row[5])]  # Convert all physInfo to floats and bool types
            info["objects"] = info["objects"] + [PhysObject(pos, pygame.image.load(row[2]).convert_alpha(),
                                                                physInfo[0], physInfo[1], physInfo[2])]

    ## LOADING THE PLAYER ##
    with open(os.path.join("levels", level, "player.csv"), "r") as file:
        reader = csv.reader(file)
        for row in reader:
            pos = tuple(map(int, row[0:2]))
            info["player"] = Player(pos, player_image, float(row[2]), float(row[3]), float(row[4]),bool(row[5]))

    ## LOADING LEVEL OBJECTIVES ##
    with open(os.path.join("levels", level, "objectives.csv"), "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == "PLAYER":
                objInfo = list(map(int, row[1:]))
                info["objectives"] = info["objectives"] + [PlayerObjective(Vec2(objInfo[0], objInfo[1]), objInfo[2], objInfo[3], info["player"])]
            elif row[0] == "PHYS":
                objInfo = list(map(int, row[1:]))
                info["objectives"] = info["objectives"] + [PhysObjective(Vec2(objInfo[0], objInfo[1]), objInfo[2], objInfo[3],
                                                                           [x for x in info["objects"] if isinstance(x, KeyObject)])]
            elif row[0] == "OBJECT":
                pos = tuple(map(int, row[1:3]))
                conv = list(map(float, row[4:]))
                colour = tuple(conv[1:4])
                info["objects"] = info["objects"] + [KeyObject(pos, pygame.image.load(row[3]).convert_alpha(), conv[0],
                                                               colour, conv[-1], conv[-2])]

    return info


class State:
    def __init__(self, newstate):
        self.state = newstate
    def newstate(self, newstate):
        self.state = newstate
    def RunFrame(self, dt):
        self.state.RunFrame(dt)

class MenuButton:
    def __init__(self, text, pos):
        self.text = text
        self.buttonText = mediumMenu.render(text, True, BLACK)
        self.buttonRect = pygame.Rect(pos[0], pos[1], swidth / 2, 50)
        self.buttonTextRect = self.buttonText.get_rect()
        self.buttonTextRect.center = self.buttonRect.center
    def Draw(self):
        if self.buttonRect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(screen, NEARLYBLACK, self.buttonRect, 0, 7)
        else:
            pygame.draw.rect(screen, GREY, self.buttonRect, 0, 7)
        pygame.draw.rect(screen, BLACK, self.buttonRect, 3, 7)
        screen.blit(self.buttonText, self.buttonTextRect)
    def collide(self, mousePos):
        return self.buttonRect.collidepoint(mousePos)

class Menu:
    def __init__(self, stateobj):
        self.state = stateobj
        self.buttonList = []
        self.DrawButton("Play Game")
        self.DrawButton("Leaderboards")
        self.DrawButton("Quit")
        self.background_image = pygame.image.load("assets/background/background.png").convert()
    def DrawButton(self, text):
        newpos = ((swidth / 4), (2 / 5 * sheight) + 60 * len(self.buttonList))
        self.buttonList.append(MenuButton(text, newpos))
    def RunFrame(self, dt):
        screen.blit(self.background_image, (0, 0))

        title = largeBoldMenu.render("Main Menu", True, ORANGE)
        titleRect = title.get_rect()
        titleRect.center = ((swidth / 2), 100)
        screen.blit(title, titleRect)

        for button in self.buttonList:
            button.Draw()

        click, _, _ = pygame.mouse.get_pressed()
        mousePos = pygame.mouse.get_pos()

        if click:
            if self.buttonList[0].collide(mousePos):
                gameData = level_load(DEBUG_LEVEL)
                world, objects, objectives, player = gameData["world"], gameData["objects"], gameData["objectives"], gameData["player"]
                self.state.newstate(Game(self.state, world, objects, player, objectives))
            elif self.buttonList[2].collide(mousePos):
                pygame.quit()
                sys.exit()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

class Game:
    def __init__(self, stateobj, world, objects, player, objectives):
        self.state = stateobj
        self.background_image = pygame.image.load("assets/background/backgroundbig.png").convert()
        self.level_size = self.background_image.get_size()
        self.lwidth, self.lheight = self.level_size

        self.world = world
        yTop = 0 - (self.lheight - sheight)
        self.world.append(WorldCollider(pygame.Rect(-1, yTop, 1, self.lheight)))
        self.world.append(WorldCollider(pygame.Rect(0, yTop - 1, self.lwidth, 1)))
        self.world.append(WorldCollider(pygame.Rect(self.lwidth, yTop, 1, self.lheight)))
        self.lPos = [0, 0]

        self.objects = objects
        self.player = player
        self.objectives = objectives

        self.colHandler = CollisionHandler(self.level_size)
        self.particleHandler = ParticleHandler()
    def DrawHUD(self):
        font = pygame.font.Font(None, 30)
        render_fps = font.render(str(int(clock.get_fps())), True, WHITE)
        screen.blit(render_fps, (0, 0))
        render_mousepos = font.render(str(pygame.mouse.get_pos()), True, WHITE)
        screen.blit(render_mousepos, (500, 0))
        fuelBackgroundRect = pygame.Rect(0, 0, int(0.75 * swidth), int(0.03 * sheight))
        fuelRect = pygame.Rect(0, 0, int(0.75 * swidth * self.player.fuel / self.player.tank), int(0.03 * sheight))

        fuelBackgroundRect.center, fuelRect.center = (swidth // 2, int(0.95 * sheight)), (swidth // 2, int(0.95 * sheight))
        pygame.draw.rect(screen, NEARLYBLACK, fuelBackgroundRect)
        pygame.draw.rect(screen, (255, lINTerp(0, 200, self.player.fuel / self.player.tank), 0), fuelRect)

    def RunFrame(self, dt):
        # Make it easier to reference everything
        background_image, world, objects, player, colHandler, particleHandler, objectives = self.background_image, \
                                                                                self.world, \
                                                                                self.objects, self.player, \
                                                                                self.colHandler, self.particleHandler, \
                                                                                self.objectives

        oldLPos = self.lPos
        self.lPos = getCameraTrack(player.GetPos(), self.lPos, background_image.get_size()[0], background_image.get_size()[1])
        world = world + objectives
        # move game objects accordingly with the level
        diff = list(numpy.subtract(self.lPos, oldLPos))  # convert the numpy array to a regular list
        player.SetPos(self.player.GetPos() + Vec2(diff))  # PhysObjects can be moved via vector addition
        for object in objects:
            object.SetPos(object.GetPos() + Vec2(diff))

        for particle in particleHandler.particles:
            particle.SetPos(particle.GetPos() + Vec2(diff))

        for wc in world:  # Worldcolliders are tracked by rects only, so use numpy list subtraction
            wc.Move(diff)
        ##############################################

        screen.blit(background_image, tuple(self.lPos))

        self.DrawHUD()

        colliders = world + objects  # Everything the player can collide with

        ## UPDATING PLAYER ##
        player.Update(colliders, dt)
        player.Draw(screen)
        ## UPDATING OBJECTIVES ##
        for objective in objectives:
            objective.Update()
            if time.time() - objective.lastEmission >= 0.1:
                particleHandler.Emit(objective, objective.colour, 3, Vec2(random.randint(-5, 5), random.randint(-15, 0)), True)
                objective.lastEmission = time.time()
            objective.Draw(screen)

        ## UPDATING PHYSOBJECTS ##
        newcolliders = [x for x in world]
        newcolliders.append(player)
        for object in objects:
            if isinstance(object, KeyObject):
                object.Update(newcolliders + [x for x in objects if x != object], dt)
            else:
                object.Update(newcolliders + [x for x in objects if x != object], dt)
            object.Draw(screen)

        if DEBUG:
            for collider in world:
                collider.DrawDebug()
        ###############################
        newcol = [x for x in objects]
        newcol.append(player)
        ## HANDLE COLLISIONS ##
        colHandler.Update(newcol)
        ## UPDATE PARTICLES ##
        particleHandler.Update(screen, objects, dt)

        keys = pygame.key.get_pressed()
        # Player Controls
        if keys[pygame.K_RIGHT]:
            player.Rotate(1, colliders)
        if keys[pygame.K_LEFT]:
            player.Rotate(-1, colliders)
        if keys[pygame.K_SPACE]:
            player.Thrust(particleHandler)

        elif keys[pygame.K_LSHIFT]:
            player.Thrust(particleHandler, True)

        if keys[pygame.K_MINUS]:
            self.lPos[0] = self.lPos[0] - 1
        elif keys[pygame.K_EQUALS]:
            self.lPos[0] = self.lPos[0] + 1

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    for object in [player] + objects:
                        object.SetWeightless(False if object.weightless else True)
            if event.type == pygame.KEYUP:  # Cleaning up drive forces
                if event.key == pygame.K_SPACE:
                    player.RemoveForce(player, "Drive")
                if event.key == pygame.K_LSHIFT:
                    player.RemoveForce(player, "Drive")


state = State(None)
menu = Menu(state)
state.newstate(menu)

prev_time = time.time()
while True:
    clock.tick()
    now = time.time()
    dt = now - prev_time
    prev_time = now

    state.RunFrame(dt)

    pygame.display.update()
    clock.tick(FPS)
