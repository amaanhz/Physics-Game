from physics import *
from constants import *
import os, csv

largeBoldMenu = pygame.font.Font(FUTURE_LIGHT, 100)
mediumMenu = pygame.font.Font(OPTIMUS, 28)
hudFont = pygame.font.Font(UNISPACE, 30)

def getCameraTrack(player, lpos, lwidth, lheight):
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
    x, y = player.GetPos()
    playerRect = player.GetRect()
    swidth, sheight = WINDOW_SIZE # Screen width and height
    halfw, halfh = swidth / 2, sheight / 2
    maxWidthOffset = lwidth - swidth # The maximum width and height the level can move before the image ends
    maxHeightOffset = lheight - sheight
    newlpos = list(lpos) # New level position will be calculated and stored in a list

    if not Rect(0, 0, swidth, sheight).contains(playerRect):
        ideal = Vec2(max(x - halfw, 0), max(y - halfh, 0))
        levelRect = Rect(0, 0, lwidth, lheight)
        idealBottomRight = ideal + Vec2(swidth, sheight)
        diff = idealBottomRight - Vec2(levelRect.bottomright)
        diff.x, diff.y = max(diff.x, 0), max(diff.y, 0)
        ideal = ideal - diff
        return [int(a) for a in ideal.Inverse()]

    if x + halfw > swidth and lpos[0] > -maxWidthOffset:
        difference = x + halfw - swidth
        newlpos[0] = lpos[0] - difference
    elif x - halfw < 0 and lpos[0] < 0:
        difference = abs(x - halfw)
        newlpos[0] = lpos[0] + difference

    if y - halfh < 0 and lpos[1] < 0:
        difference = abs(y - halfh)
        newlpos[1] = lpos[1] + difference
    elif y + halfh > sheight and lpos[1] > -maxHeightOffset:
        difference = y + halfh - sheight
        newlpos[1] = lpos[1] - difference
    return [int(a) for a in newlpos]

def level_load(level):
    ## All level info stored as a dictionary
    info = {
        "background": os.path.join("levels", level, "background.png"),
        "world": [],
        "objects": [],
        "objectives": [],
        "obstacles": [],
        "hazards": [],
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

    ## LOADING OBSTACLES ##
    with open(os.path.join("levels", level, "obstacles.csv"), "r") as file:
        reader = csv.reader(file)
        for row in reader:
            objInfo = list(map(int, row))  # Convert all coordinate values for the rect into integers
            pos = Vec2(objInfo[0], objInfo[1])
            info["obstacles"] = info["obstacles"] + [Obstacle(pos, objInfo[2], objInfo[3], info["player"])]

    ## LOADING HAZARDS (AIRSTREAMS) ##
    with open(os.path.join("levels", level, "hazards.csv"), "r") as file:
        reader = csv.reader(file)
        for row in reader:
            objInfo = list(map(int, row))  # Convert all coordinate values for the rect into integers
            pos = Vec2(objInfo[0], objInfo[1])
            force = Vec2(objInfo[-2], objInfo[-1])
            info["hazards"] = info["hazards"] + [AirStream(pos, objInfo[2], objInfo[3], objInfo[4], objInfo[5], force)]


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
                background, world, objects, objectives, obstacles, hazards, player = gameData["background"], gameData["world"], \
                    gameData["objects"], gameData["objectives"], gameData["obstacles"], gameData["hazards"], gameData["player"]
                self.state.newstate(Game(self.state, background, world, objects, player, objectives, obstacles, hazards))
            elif self.buttonList[2].collide(mousePos):
                pygame.quit()
                sys.exit()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

class Timer:
    def __init__(self, pos, active=True):
        self.pos = pos
        self.epoch = time.time()
        self.formattedTime = ""
        self.elapsed = 0
        self.active = active
    def Update(self):
        if self.active:
            self.elapsed = time.time() - self.epoch
            minutes = int(self.elapsed // 60)
            secondsRemaining = int(self.elapsed - minutes * 60)
            self.formattedTime = f"{'0' if minutes < 10 else ''}{str(minutes)}:{'0' if secondsRemaining < 10 else ''}{str(secondsRemaining)}"
    def Draw(self):
        render_time = hudFont.render(self.formattedTime, True, WHITE)
        screen.blit(render_time, self.pos)


class Game:
    def __init__(self, stateobj, background, world, objects, player, objectives, obstacles, hazards):
        self.state = stateobj
        self.background_image = pygame.image.load(background).convert_alpha()
        self.level_size = self.background_image.get_size()
        self.lwidth, self.lheight = self.level_size

        self.world = world
        self.world.append(WorldCollider(pygame.Rect(-1, 0, 1, self.lheight)))
        self.world.append(WorldCollider(pygame.Rect(0, -1, self.lwidth, 1)))
        self.world.append(WorldCollider(pygame.Rect(self.lwidth, 0, 1, self.lheight)))
        self.lPos = [0, 0]

        self.objects = objects
        self.player = player
        self.objectives = objectives
        self.obstacles = obstacles
        self.hazards = hazards

        self.colHandler = CollisionHandler(self.level_size)
        self.particleHandler = ParticleHandler()
        self.timer = Timer((0,0))
    def DrawHUD(self):
        font = pygame.font.Font(None, 30)
        #render_fps = font.render(str(int(clock.get_fps())), True, WHITE)
        #screen.blit(render_fps, (0, 0))
        render_mousepos = font.render(str(pygame.mouse.get_pos()), True, WHITE)
        screen.blit(render_mousepos, (500, 0))
        fuelBackgroundRect = pygame.Rect(0, 0, int(0.75 * swidth), int(0.03 * sheight))
        fuelRect = pygame.Rect(0, 0, int(0.75 * swidth * self.player.fuel / self.player.tank), int(0.03 * sheight))

        fuelBackgroundRect.center, fuelRect.center = (swidth // 2, int(0.95 * sheight)), (swidth // 2, int(0.95 * sheight))
        pygame.draw.rect(screen, NEARLYBLACK, fuelBackgroundRect)
        pygame.draw.rect(screen, (255, lINTerp(0, 200, self.player.fuel / self.player.tank), 0), fuelRect)

    def RunFrame(self, dt):
        # Make it easier to reference everything
        background_image, world, objects, player, colHandler, particleHandler, objectives, obstacles, hazards = \
            self.background_image, \
            self.world, self.objects, self.player, self.colHandler, self.particleHandler, self.objectives, \
            self.obstacles, self.hazards

        self.timer.Update()

        world = world + objectives + obstacles + hazards
        colliders = world + objects  # Everything the player can collide with

        oldLPos = self.lPos
        self.lPos = getCameraTrack(player, self.lPos, background_image.get_size()[0], background_image.get_size()[1])

        # move game objects accordingly with the level
        diff = Vec2(list(numpy.subtract(self.lPos, oldLPos)))  # convert the numpy array to a regular list and then to a Vec2

        if not Rect(0, 0, swidth, sheight).contains(player.GetRect()):
            player.SetPos(player.GetPos() + diff)
            for object in objects:
                object.SetPos(object.GetPos() + diff)
            for particle in particleHandler.particles:
                particle.SetPos(particle.GetPos() + diff)
            for wc in world:
                wc.Move(diff)
        else:
            CollisionHandler.SafeMove(player, world, diff)
            for wc in world:
                wc.Move(diff)

            for object in objects:
                CollisionHandler.SafeMove(object, world, diff)

            for particle in particleHandler.particles:
                #CollisionHandler.SafeMove(particle, world, diff)
                particle.SetPos(particle.GetPos() + diff)


        ##############################################

        screen.blit(background_image, tuple(self.lPos))

        self.timer.Draw()
        self.DrawHUD()

        particleHandler.Update(screen, colliders + [player], dt)

        for hazard in hazards:
            hazard.Update(objects + [player])
            hazard.Draw(screen)

        ## UPDATING OBJECTIVES ##
        for obstacle in obstacles:
            obstacle.Update(player)
            obstacle.Draw(screen)

        for objective in objectives:
            objective.Update()
            objective.Draw(screen)

        ## UPDATING PLAYER ##
        player.Update(colliders, dt)
        player.Draw(screen)

        ## UPDATING PHYSOBJECTS ##
        newcolliders = [x for x in world]
        newcolliders.append(player)
        for object in objects:
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
