from physics import *
from constants import *
import os, csv

largeBoldMenu = pygame.font.Font(QUALY, 100)
slightlylargeBold = pygame.font.Font(EXO, 75)
mediumText = pygame.font.Font(EXO, 50)
mediumSmallText = pygame.font.Font(EXO, 30)
smallText = pygame.font.Font(EXO, 20)
mediumMenu = pygame.font.Font(EXO, 28)
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
    level = str(level)
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
                info["objectives"] = info["objectives"] + [PlayerObjective(Vec2(objInfo[0], objInfo[1]), objInfo[2], objInfo[3])]
            elif row[0] == "PHYS":
                objInfo = list(map(int, row[1:]))
                info["objectives"] = info["objectives"] + [PhysObjective(Vec2(objInfo[0], objInfo[1]), objInfo[2], objInfo[3])]
            elif row[0] == "OBJECT":
                pos = tuple(map(int, row[1:3]))
                conv = list(map(float, row[4:]))
                colour = tuple(conv[1:4])
                info["objects"] = info["objects"] + [KeyObject(pos, pygame.image.load(row[3]).convert_alpha(), conv[0],
                                                               colour, conv[-2], conv[-1])]

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

def gameInit(levelnum, stateobj):
    gameData = level_load(levelnum)
    background, world, objects, objectives, obstacles, hazards, player = gameData["background"], gameData[
        "world"], gameData["objects"], gameData["objectives"], gameData["obstacles"], gameData["hazards"], \
                                                                         gameData["player"]
    return Game(stateobj, background, world, objects, player, objectives, obstacles, hazards, levelnum)

def textRender(font, pos, text, colour):
    rendered = font.render(text, True, colour)
    rect = rendered.get_rect()
    rect.center = pos
    screen.blit(rendered, rect)

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
    @staticmethod
    def formatTime(sec):
        minutes = int(sec // 60)
        secondsRemaining = int(sec - minutes * 60)
        return f"{'0' if minutes < 10 else ''}{str(minutes)}:{'0' if secondsRemaining < 10 else ''}{str(secondsRemaining)}"
    def Draw(self):
        render_time = hudFont.render(self.formattedTime, True, WHITE)
        screen.blit(render_time, self.pos)
    def GetTime(self):
        return self.elapsed

class State:
    def __init__(self, newstate):
        self.state = newstate
    def newstate(self, newstate):
        self.state = newstate
    def RunFrame(self, dt):
        self.state.RunFrame(dt)

class MenuButton:
    def __init__(self, text, pos, width=swidth/2, height=50):
        self.text = text
        self.buttonText = mediumMenu.render(text, True, BLACK)
        self.buttonRect = pygame.Rect(pos[0], pos[1], width, height)
        self.buttonTextRect = self.buttonText.get_rect()
        self.buttonTextRect.center = self.buttonRect.center
        self.enabled = True
    def Draw(self):
        if self.enabled:
            if self.buttonRect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, NEARLYBLACK, self.buttonRect, 0, 7)
            else:
                pygame.draw.rect(screen, GREY, self.buttonRect, 0, 7)
            pygame.draw.rect(screen, BLACK, self.buttonRect, 3, 7)
            screen.blit(self.buttonText, self.buttonTextRect)
    def collide(self, mousePos):
        return self.buttonRect.collidepoint(mousePos)
    def setEnabled(self, val):
        self.enabled = val


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
        screen.fill(BACKGROUNDCOLOUR)

        textRender(largeBoldMenu, ((swidth / 2), 100), "PhysX", ORANGE)

        for button in self.buttonList:
            button.Draw()

        click, _, _ = pygame.mouse.get_pressed()
        mousePos = pygame.mouse.get_pos()

        if click:
            if self.buttonList[0].collide(mousePos):
                self.state.newstate(gameInit(DEBUG_LEVEL, self.state))
            elif self.buttonList[2].collide(mousePos):
                pygame.quit()
                sys.exit()

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

class ScoringScreen:
    def __init__(self, stateobj, objectives, timer, collisions, levelnum):
        self.state = stateobj
        self.totalobj = len(objectives)
        self.objmet = len([x for x in objectives if x.complete])
        self.optimal = OPTIMALS[levelnum]
        self.time = int(timer)
        self.collisions = collisions
        self.levelnum = levelnum
        self.background_image = pygame.image.load("assets/background/background.png").convert()

        if self.objmet == self.totalobj: # if the player succeeded
            timeDiff = self.optimal - timer # This will be negative if the player took longer than the optimal
            timeMult = min(abs(timeDiff) / self.optimal, 1) # Only penalise/bonus for up to double the time and down to 0 seconds
            timeMult *= -1 if timeDiff < 0 else 1 # Bonus or penalty
            self.score = int(SCOREBASE + (SCOREBASE*timeMult) - (HITPENALTY * collisions))
            self.score = 1 if self.score <= 0 else self.score
        else:
            self.score = 0

        self.buttonList = [MenuButton("Replay", (swidth/5, sheight * (3/5)), swidth/4),
                           MenuButton("Next Level", (swidth/5, sheight * (3/5) + 60), swidth/4),
                           MenuButton("Main Menu", (swidth * (3/5), sheight * (3/5)), swidth/4),
                           MenuButton("Save Score", (swidth * (3/5), sheight * (3/5) + 60), swidth/4)]
        if len(OPTIMALS) < levelnum + 1:
            self.buttonList[1].setEnabled(False)
        if self.score <= 0:
            self.buttonList[3].setEnabled(False)


    def detailRender(self, detail, value, colour):
        textRender(mediumText, ((swidth / 2), 220 + (self.detailnum * 60)), f"{detail}: {str(value)}", colour)
        self.detailnum += 1

    def RunFrame(self, dt):
        screen.fill(BACKGROUNDCOLOUR)
        textRender(slightlylargeBold, ((swidth / 2), 100), f"Score: {str(self.score)}", WHITE)

        self.detailnum = 0

        colour = WHITE
        if self.objmet < self.totalobj:
            colour = RED
        textRender(mediumText, ((swidth / 2), 220 + (self.detailnum * 60)), f"Objectives Met: {str(self.objmet)}/{str(self.totalobj)}", colour)
        self.detailnum += 1

        colour = WHITE
        if self.time < self.optimal:
            colour = GREEN
        elif self.time > self.optimal:
            colour = RED
        self.detailRender("Time", Timer.formatTime(self.time), colour)


        colour = WHITE
        if self.collisions > 0:
            colour = RED
        textRender(mediumText, ((swidth / 2), 220 + (self.detailnum * 60)),
                   f"Damaging Collisions: {str(self.collisions)} ({str(-1 * self.collisions * HITPENALTY)})", colour)
        self.detailnum += 1


        for button in self.buttonList:
            button.Draw()

        click, _, _ = pygame.mouse.get_pressed()
        mousePos = pygame.mouse.get_pos()

        if click:
            if self.buttonList[0].collide(mousePos):
                self.state.newstate(gameInit(self.levelnum, self.state))
            elif self.buttonList[1].collide(mousePos) and len(OPTIMALS) >= self.levelnum + 1:
                self.state.newstate(gameInit(self.levelnum + 1, self.state))
            elif self.buttonList[2].collide(mousePos):
                self.state.newstate(Menu(self.state))
            elif self.buttonList[3].collide(mousePos) and self.score > 0:
                self.state.newstate(SaveScore(self.state, self.score, self.levelnum))

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

class SaveScore:
    def __init__(self, stateobj, score, levelnum):
        self.state = stateobj
        self.score = score
        self.level = levelnum
        self.text = ''
        self.error = ''
    def filterName(self):
        if len(self.text) >= 40:
            self.error = "This username is too long. It must be less than 40 characters."
            return False
        if len(self.text) == 0:
            self.error = "Please enter a name."
            return False
        if not self.text[0].isalpha():
            self.error = "The first character of the name must be alphabetic."
            return False
        self.error = ""
        return True

    def recordScore(self, user, score):
        pass

    def RunFrame(self, dt):
        screen.fill(BACKGROUNDCOLOUR)

        textRender(slightlylargeBold, ((swidth / 2), 100), f"Score: {str(self.score)}", WHITE)

        inputBoxWidth = swidth * (4/5)
        inputBoxHeight = 80
        inputBox = pygame.Rect((swidth/2) - (inputBoxWidth/2), (sheight/2) - (inputBoxHeight/2), inputBoxWidth, inputBoxHeight)
        pygame.draw.rect(screen, WHITE, inputBox)

        textRender(mediumText, tuple(Vec2(inputBox.center) - Vec2(0, 100)), "Enter a username:", WHITE)

        textRender(mediumSmallText, inputBox.center, self.text, BLACK)

        if len(self.error) > 0:
            textRender(smallText, tuple(Vec2(inputBox.center) + Vec2(0, 100)), self.error, RED)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.filterName():
                        print(self.text)
                        self.state.newstate(Menu(self.state))
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1] if self.text != '' else ''
                elif event.key == pygame.K_SPACE:
                    pass
                else:
                    if len(self.text) <= 40:
                        self.text += event.unicode
            if event.type == QUIT:
                pygame.quit()
                sys.exit()


class Game:
    def __init__(self, stateobj, background, world, objects, player, objectives, obstacles, hazards, levelnum):
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
        self.levelnum = levelnum

    def DrawHUD(self):
        self.timer.Draw()

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

        self.DrawHUD()

        particleHandler.Update(screen, colliders + [player], dt)

        for hazard in hazards:
            hazard.Update(objects + [player])
            #hazard.Draw(screen)

        ## UPDATING OBJECTIVES ##
        completed = True
        for objective in objectives:
            objective.Update([player] if isinstance(objective, PlayerObjective)
                             else [x for x in objects if isinstance(x, KeyObject)])
            if not objective.complete:
                completed = False
            objective.Draw(screen)
        if completed:
            self.state.newstate(ScoringScreen(self.state, objectives, self.timer.GetTime(), player.collisions, self.levelnum))


        for obstacle in obstacles:
            if obstacle.Update(player):
                self.state.newstate(ScoringScreen(self.state, objectives, self.timer.GetTime(), player.collisions, self.levelnum))
            obstacle.Draw(screen)

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
            player.Rotate(1, colliders, dt)
        if keys[pygame.K_LEFT]:
            player.Rotate(-1, colliders, dt)
        if keys[pygame.K_SPACE]:
            player.Thrust(particleHandler)

        #elif keys[pygame.K_LSHIFT]:
        #    player.Thrust(particleHandler, True)

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
