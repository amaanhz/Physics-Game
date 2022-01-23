from physics import *
from constants import *
import os

largeBoldMenu = pygame.font.Font(FUTURE_LIGHT, 100)
mediumMenu = pygame.font.Font(OPTIMUS, 28)

def getCameraTrack(pos, lpos, lwidth , lheight):
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
        pygame.draw.rect(screen, GREY, self.buttonRect, 0, 7)
        pygame.draw.rect(screen, BLACK, self.buttonRect, 4, 7)
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
                objects = [PhysObject((100, 100), ball_image, 150, SPHERE_DRAG_COEFFICIENT, True, 0.35)]
                for i in range(0, 5):
                    objects.append(PhysObject((random.randint(0, swidth - ball_image.get_width()),
                                               random.randint(0, sheight - ball_image.get_height())), ball_image, 150,
                                              SPHERE_DRAG_COEFFICIENT, True, 0.35))
                player = Player((50, 100), player_image, 100)

                world = [WorldCollider(pygame.Rect(0, 474, 1279, 720 - 474))]
                self.state.newstate(Game(self.state, world, objects, player))

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

class Game:
    def __init__(self, stateobj, world, objects, player):
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

        self.colHandler = CollisionHandler(self.level_size)
        self.particleHandler = ParticleHandler()
    def RunFrame(self, dt):
        background_image, world, objects, player, colHandler, particleHandler = self.background_image, self.world, \
                                                                                self.objects, self.player, \
                                                                                self.colHandler, self.particleHandler

        oldLPos = self.lPos
        self.lPos = getCameraTrack(player.GetPos(), self.lPos, background_image.get_size()[0], background_image.get_size()[1])

        # move game objects accordingly with the level
        diff = list(numpy.subtract(self.lPos, oldLPos))  # convert the numpy array to a regular list
        player.SetPos(self.player.GetPos() + Vec2(diff))  # PhysObjects can be moved via vector addition
        for object in objects:
            object.SetPos(object.GetPos() + Vec2(diff))
        for particle in particleHandler.particles:
            particle.SetPos(particle.GetPos() + Vec2(diff))
        for wc in world:  # Worldcolliders are tracked by rects only, so use numpy list subtraction
            wc.Move(diff)

        screen.blit(background_image, tuple(self.lPos))

        font = pygame.font.Font(None, 30)
        render_fps = font.render(str(int(clock.get_fps())), True, WHITE)
        screen.blit(render_fps, (0, 0))
        render_mousepos = font.render(str(pygame.mouse.get_pos()), True, WHITE)
        screen.blit(render_mousepos, (500, 0))

        colliders = world + objects  # Everything the player can collide with

        ## UPDATING ALL GAME OBJECTS ##
        player.Update(colliders, dt)
        player.Draw(screen)

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
        colHandler.Update(newcol)

        particleHandler.Update(dt)

        keys = pygame.key.get_pressed()
        # Player Controls
        if keys[pygame.K_RIGHT]:
            player.Rotate(1, colliders)
        if keys[pygame.K_LEFT]:
            player.Rotate(-1, colliders)
        if keys[pygame.K_SPACE]:
            base = Vec2(0, PLAYERFORCE)
            rads = player.angle * RAD
            base.x, base.y = (base.x * math.cos(rads)) - (base.y * math.sin(rads)), \
                             -((base.x * math.sin(rads)) + (base.y * math.cos(rads)))
            player.AddForce(player, "Drive", base)
            recoil = base.Inverse().GetNormalized()
            for i in range(0, 10):
                x, y = tuple(player.engine)
                uv = recoil * 5 + random.randint(-6, 6)
                particleHandler.Add(EngineParticle(player.engine, uv, random.uniform(0.5, 1.5)))

        elif keys[pygame.K_LSHIFT]:
            base = Vec2(0, PLAYERFORCE)
            rads = player.angle * RAD
            base.x, base.y = -((base.x * math.cos(rads)) - (base.y * math.sin(rads))), \
                             (base.x * math.sin(rads)) + (base.y * math.cos(rads))
            player.AddForce(player, "Drive", base)

        if keys[pygame.K_MINUS]:
            lPos[0] = lPos[0] - 1
        elif keys[pygame.K_EQUALS]:
            lPos[0] = lPos[0] + 1

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
                if event.key == pygame.K_j:
                    ball.RemoveForce(ball, "Drive")
                if event.key == pygame.K_h:
                    ball.RemoveForce(ball, "Drive")


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
