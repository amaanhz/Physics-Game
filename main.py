import pygame, time, numpy, math, sys, copy

clock = pygame.time.Clock()

from pygame.locals import *
pygame.init()

pygame.display.set_caption("Physics")

DEBUG = False

WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

WINDOW_SIZE = (1280, 720)
FPS = 100

RAD = math.pi / 180

GRAVITY = 15
AIR_DENSITY = 1.2041
PLAYER_DRAG_COEFFICIENT = 1.15
SPHERE_DRAG_COEFFICIENT = 0.5
PLAYER_ROTATION_SPEED = 1



class Material:
    def __init__(self, static, kinetic):
        self.static = static
        self.kinetic = kinetic

MATERIALS = {
    "Asphalt": Material(0.9, 0.65)
}

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)

background_image = pygame.image.load("assets/background/backgroundbig.png").convert()
player_image = pygame.image.load("assets/sprites/character.png").convert_alpha()
ball_image = pygame.image.load("assets/sprites/ball.png").convert_alpha()

METRE = player_image.get_height() * (1 / 1.7)

def coltest(rect, colliders):
    hit_list = []
    for collider in colliders:
        if rect.colliderect(collider.GetRect()):
            hit_list.append(collider)
    return hit_list

def touching(obj1, obj2):
    rect1, rect2 = obj1.GetRect(), obj2.GetRect()
    if rect1.left == rect2.right:
        return "left"
    if rect1.right == rect2.left:
        return "right"
    if rect1.top == rect2.bottom:
        return "top"
    if rect1.bottom == rect2.top:
        return "bottom"
    return False

def touchingany(ent, colliders):
    entRect = ent.GetRect()
    entsides = [entRect.left, entRect.top, entRect.right, entRect.bottom]
    collisions = []
    for obj in colliders:
        rect = obj.GetRect()
        checky = (rect.top <= entRect.bottom and rect.bottom >= entRect.top)
        checkx = (rect.left <= entRect.right and rect.right >= entRect.left)
        if entRect.left == rect.right and checky:
            collisions.append((obj, "left"))
        if entRect.top == rect.bottom and checkx:
            collisions.append((obj, "top"))
        if entRect.right == rect.left and checky:
            collisions.append((obj, "right"))
        if entRect.bottom == rect.top and checkx:
            collisions.append((obj, "bottom"))
    return collisions

def identity(n):
    if n != 0:
        return n / abs(n)
    else:
        return n

class Vec2:
    def __init__(self, *args):
        if len(args) == 1 and (isinstance(args[0], tuple) or isinstance(args[0], list)):
            self.x, self.y = args[0]
        elif len(args) == 2:
            self.x, self.y = args[0], args[1]

    def __add__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x + n.x, self.y + n.y)
        return Vec2(self.x + n, self.y + n)
    def __radd__(self, n):
        return self + n

    def __sub__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x + n.x, self.y + n.y)
        return Vec2(self.x + n, self.y + n)
    def __eq__(self, v2):
        return self.x == v2.x and self.y == v2.y
    def __mul__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x * n.x, self.y * n.y)
        return Vec2(self.x * n, self.y * n)
    def __truediv__(self, n):
        return Vec2(self.x / n, self.y / n)
    def __floordiv__(self, n):
        return Vec2(self.x // n, self.y // n)
    def __pow__(self, pow):
        return Vec2(self.x ** pow, self.y ** pow)
    def __str__(self):
        return f"{str(self.x)}, {str(self.y)}"
    def __round__(self, n):
        return Vec2(round(self.x, n), round(self.y, n))
    def Set(self, x, y):
        self.x, self.y = x, y
    def SetX(self, x):
        self.x = x
    def GetX(self):
        return self.x
    def SetY(self, y):
        self.y = y
    def GetY(self):
        return self.y
    def SetVec2(self, v2):
        self.x, self.y = v2.x, v2.y
    def GetSqrMag(self):
        return self.x ** 2 + self.y ** 2
    def GetMag(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    def GetNormalized(self):
        mag = self.GetMag()
        return self / mag
    def Inverse(self):
        return self * -1


dir = {"left" : Vec2(-1, 0),
       "top" : Vec2(0, -1),
       "right" : Vec2(1, 0),
       "bottom" : Vec2(0, 1)}


class Force(Vec2):
    def __init__(self, source, name, *args):
        self.source = source
        self.name = name
        if len(args) == 1:
            self.x, self.y = args[0].x, args[0].y
        if len(args) == 2:
            self.x, self.y = args[0], args[1]

class ForceManager:
    def __init__(self, parent):
        self.forces = []
        self.parent = parent
        self.rForce = Vec2(0, 0)

    def GetForce(self, source, name):
        t = [x for x in self.forces if x.name == name and x.source == source] # Quick method of searching the list
        if len(t) > 1:
            return t
        elif len(t) == 1:
            return t[0]
        else:
            return None

    def GetAnyForce(self, name):
        t = [x for x in self.forces if x.name == name]
        if len(t) > 0:
            return t
        else:
            return None

    def AddForce(self, source, name, *args):
        vec = Vec2(0, 0)
        if len(args) == 2:
            vec.Set(args[0], args[1])
        else:
            vec = args[0]
        if round(vec, 1) != Vec2(0, 0):
            if self.GetForce(source, name) is None:
                self.forces.append(Force(source, name, vec))
            else:
                self.RemoveForce(source, name)
                self.forces.append(Force(source, name, vec))
        else:
            self.RemoveForce(source, name)

    def RemoveForce(self, *args):
        if len(args) == 2:
            source, name = args
            for i, force in enumerate(self.forces):
                if force.source == source and force.name == name:
                    self.forces.pop(i)
        else:
            self.forces.pop(self.forces.index(args[0]))

    def GetResultantNOF(self):
        rForce = Vec2(0, 0)
        for force in self.forces:
            if "Friction" not in force.name and force.name != "Air Resistance":
                rForce += force
        return rForce


    def Update(self, colliders, dt):
        parent = self.parent
        v = parent.velocity

        touching = touchingany(parent, colliders)
        touchingEnts = [x[0] for x in touching]

        rForce = self.GetResultantNOF()  # Alternative rForce where we ignore drag forces

        ## REMOVE REDUNDANT FORCES FROM ENTITIES NOT IN CONTACT/NOT OURSELF OR NOT APPLICABLE ##
        for i, force in enumerate(self.forces):
            # Contact Check (applies to any force)
            if force.source not in touchingEnts and force.source != self.parent:
                self.forces.pop(i)

            # Friction Check
            if force.name == "FrictionX":
                if v.x == 0 and rForce.x == 0:
                    self.forces.pop(i)
            if force.name == "FrictionY":
                if v.y == 0 and rForce.y == 0:
                    self.forces.pop(i)


        ## ADD WEIGHT FORCE IF IT DOESN'T EXIST ##
        if not parent.weightless and not self.GetForce(parent, "Weight"):
            self.AddForce(parent, "Weight", 0, parent.mass * GRAVITY)


        ## ADD NORMAL FORCE IF THERE IS AN OPPOSING FORCE ##
        for result in touching:
            ent, side = result
            ## Handle a collision with a PhysObject ##
            if not isinstance(ent, WorldCollider):
                if side == "left" or side == "right":
                    if identity(rForce.x) == dir[side].x:
                        ent.AddForce(parent, "CollisionX", Vec2(rForce.x, 0))
                    else:
                        initialparentv = parent.velocity.x
                        initialentv = ent.velocity.x
                        parent.velocity.x = -(parent.mass/ent.mass) * initialentv
                        ent.velocity.x = -(ent.mass/parent.mass) * initialparentv
                if side == "top" or side == "bottom":
                    if identity(rForce.y) == dir[side].y:
                        ent.AddForce(parent, "CollisionY", Vec2(0, rForce.y))
                    else:
                        initialparentv = parent.velocity.y
                        initialentv = ent.velocity.y
                        parent.velocity.y = -(parent.mass/ent.mass) * initialentv
                        ent.velocity.y = -(ent.mass/parent.mass) * initialparentv


            if side == "left" or side == "right" and identity(rForce.x) == dir[side].x:
                self.AddForce(ent, "ReactionX", -rForce.x, 0)
            elif side == "top" or side == "bottom" and identity(rForce.y) == dir[side].y:
                self.AddForce(ent, "ReactionY", 0, -rForce.y)

        ## ADD AIR RESISTANCE ##
        if v.GetSqrMag() > 0:  # If moving
            A = 0
            if v.x > v.y:  # Simplify cross-sectional area calculation - If horizontal > vertical v, take height as A
                A = parent.rect.height / METRE
            else:
                A = parent.rect.width / METRE
            dragmag = v.GetSqrMag() * 0.5 * AIR_DENSITY * parent.Cd * A
            drag = v.GetNormalized().Inverse() * dragmag  # Turn drag magnitude into an opposite-facing vector to velocity
            parent.AddForce(parent, "Air Resistance", drag)

        ## ADD FRICTION ##
        for result in touching:
            ent, side = result
            if isinstance(ent, WorldCollider):
                if self.GetForce(ent, "ReactionY") or self.GetForce(ent, "ReactionX"):
                    N = abs(self.GetForce(ent, "ReactionY").y) if side == "top" or side == "bottom" else abs(self.GetForce(ent, "ReactionX").x)
                    threshold = ent.GetMuStatic() * N
                    kinetic = ent.GetMuKinetic()

                    if side == "top" or side == "bottom":
                        # X friction
                        if v.x != 0 or rForce.x != 0:  # Ensure the object is moving or trying to move
                            scale = -(identity(rForce.GetNormalized().x)) if v.x == 0 else -(identity(v.x))  # Determine the direction for friction to act, first from the force, otherwise from velocity.
                            if v.x == 0 and rForce.x != 0:  # If the object is not moving but is trying to move
                                if abs(rForce.x) < threshold:
                                    self.AddForce(ent, "FrictionX", Vec2(-rForce.x, 0))  # Apply static friction
                                else:
                                    self.AddForce(ent, "FrictionX", Vec2(scale * N * kinetic, 0))  # Apply kinetic friction
                            elif v.x != 0:  # If the object is moving
                                self.AddForce(ent, "FrictionX", Vec2(scale * N * kinetic, 0))

                    elif side == "left" or side == "right":
                        # Y friction
                        if v.y != 0 or rForce.y != 0:  # Ensure the object is moving or trying to move
                            scale = -(identity(rForce.GetNormalized().y)) if v.y == 0 else -(identity(v.y))  # Determine the direction for friction to act, first from the force, otherwise from velocity.
                            if v.y == 0 and rForce.y != 0:  # If the object is not moving but is trying to move
                                if rForce.y < threshold:
                                    self.AddForce(ent, "FrictionY", Vec2(0, -rForce.y))  # Apply static friction
                                else:
                                    self.AddForce(ent, "FrictionY", Vec2(0, scale * N * kinetic))  # Apply kinetic friction
                            elif v.y != 0:  # If the object is moving
                                self.AddForce(ent, "FrictionY", Vec2(0, scale * N * kinetic))

        ## RECALCULATING RESULTANT FORCE ##
        self.rForce.Set(0, 0)
        for force in self.forces:
            self.rForce += force  # Sum all the forces acting on the body

        parent.acceleration = self.rForce / parent.mass
        resultantv = parent.velocity + parent.acceleration * dt

        #### PREVENT FRICTION CAUSING OPPOSING MOTION ####
        frictionX = self.GetAnyForce("FrictionX")
        frictionY = self.GetAnyForce("FrictionY")

        if resultantv.x != 0 and frictionX:
            friction = sum(frictionX)
            if (identity(resultantv.x)) == (identity(friction.x)):  # If the resultant velocity is in the same direction as the friction
                for force in frictionX:
                    self.RemoveForce(force)
                    self.rForce -= friction  # Remove and ignore the frictional force - recalulate resultant force and acceleration before moving on

        if resultantv.y != 0 and frictionY:
            friction = sum(frictionY)
            if (identity(resultantv.y)) == (identity(friction.y)):  # If the resultant velocity is in the same direction as the friction
                for force in frictionY:
                    self.RemoveForce(force)
                    self.rForce -= friction  # Remove and ignore the frictional force - recalulate resultant force and acceleration before moving on

        parent.rForce = self.rForce
        parent.acceleration = parent.rForce / parent.mass

        #########################################
        if DEBUG:
            for force in self.forces:
                print(f"    {force.name}: {force} -- SOURCE: {force.source}")

        #########################################

class WorldCollider:
    def __init__(self, rect, material="Asphalt"):
        self.rect = rect
        self.material = MATERIALS[material]
    def GetRect(self):
        return self.rect
    def GetPos(self):
        return self.rect.topleft
    def Move(self, delta):
        self.rect.topleft = tuple(numpy.add(self.GetPos(), delta))
    def GetMaterial(self):
        return self.material
    def GetMuStatic(self):
        return self.material.static
    def GetMuKinetic(self):
        return self.material.kinetic

class PhysObject:
    def __init__(self, pos, image, mass, Cd=0.5, circular=False, COR=0):
        self.pos = Vec2(pos[0], pos[1])
        self.angle = 0
        self.angleDir = Vec2(-math.cos((90 - self.angle) * (math.pi / 180)), math.sin((90 - self.angle) * (math.pi / 180)))
        self.image_clean = image
        self.image = image
        self.rect = pygame.Rect(pos[0], pos[1], self.image.get_width(), self.image.get_height())
        self.mass = mass
        self.Cd = Cd
        self.circular = circular
        self.COR = COR
        self.weightless = False
        self.forces = ForceManager(self)
        self.rForce = Vec2(0, 0)
        self.acceleration = Vec2(0, 0)
        self.velocity = Vec2(0, 0)
        self.momentum = Vec2(0, 0)
        self.ReactionXInfo = None
        self.ReactionYInfo = None

    def Draw(self, surface):
        surface.blit(self.image, self.rect.topleft)
        if DEBUG:
            pygame.draw.rect(screen, RED, self.rect, 1)
            image_rect = self.image.get_rect()
            image_rect.center = self.rect.center
            pygame.draw.rect(screen, YELLOW, image_rect, 1)

    def GetPos(self):
        return self.pos

    def SetPos(self, p):
        self.pos = p

    def GetRect(self):
        return self.rect

    def Rotate(self, scale, colliders):
        if len(touchingany(self, colliders)) == 0:
            scale *= -1 # We want to interpret + rotation as clockwise
            self.angle += PLAYER_ROTATION_SPEED * scale
            rotated_image = pygame.transform.rotate(self.image_clean, self.angle)
            self.image = rotated_image
            if not self.circular:
                self.rect = self.image.get_rect(topleft=self.rect.topleft)
            self.angleDir.x, self.angleDir.y = -math.cos((90 - self.angle) * RAD), math.sin((90 - self.angle) * RAD)

    def Update(self, colliders, dt):
        if DEBUG:
            print(type(self))

        self.forces.Update(colliders, dt)
        self.velocity += self.acceleration * dt

        if round(self.velocity.x, 1) == 0 and identity(self.velocity.x) != identity(self.rForce.x): # If velocity is basically 0, and velocity is opposing the direction of
            self.velocity.x = 0                                                                        # resultant force, set this velocity to exactly 0.
        if round(self.velocity.y, 1) == 0 and identity(self.velocity.y) != identity(self.rForce.y):
            self.velocity.y = 0

        ##################################################
        if DEBUG:
            print(f"Resultant Force: {str(self.rForce)}")
            print(f"Acceleration: {str(self.acceleration)}")
            print(f"Velocity: {str(self.velocity)}")
            print(f"Momentum: {str(self.momentum)}")
            print(f"Angle: {str(self.angle)}")
            print(f"Angle Vector: {str(self.angleDir)}")

        ##################################################

        self.momentum = self.velocity * self.mass

        collision_types = {"top": False, "bottom": False, "left": False, "right": False}


        ## HANDLE X MOVEMENT ##
        prevposx = self.pos.x
        self.pos.x += self.velocity.x * dt * METRE
        self.rect.x = round(self.pos.x)
        hit_list = coltest(self.rect, colliders)

        for entity in hit_list:
            if self.velocity.x > 0:
                self.rect.right = entity.GetRect().left
                self.pos = Vec2(self.rect.topleft)
                collision_types["right"] = True

            elif self.velocity.x < 0:
                self.rect.left = entity.GetRect().right
                self.pos = Vec2(self.rect.topleft)
                collision_types["left"] = True

            if isinstance(entity, WorldCollider):
                if self.COR > 0:
                    bounce = abs(self.velocity.x) * self.COR
                    if bounce > 1:
                        self.velocity.x *= -1 * self.COR
                    else:
                        self.velocity.x = 0
                else:
                    self.velocity.x = 0
        #######################################
        if DEBUG:
            print(f"Rect X: {self.rect.x}")
        #######################################

        ## HANDLE Y MOVEMENT ##
        prevposy = self.pos.y
        self.pos.y += self.velocity.y * dt * METRE
        self.rect.y = round(self.pos.y)
        hit_list = coltest(self.rect, colliders)

        for entity in hit_list:
            if self.velocity.y > 0:
                self.rect.bottom = entity.GetRect().top
                self.pos = Vec2(self.rect.topleft)
                collision_types["bottom"] = True

            elif self.velocity.y < 0:
                self.rect.top = entity.GetRect().bottom
                self.pos = Vec2(self.rect.topleft)
                collision_types["top"] = True

            if isinstance(entity, WorldCollider):
                if self.COR > 0:
                    bounce = abs(self.velocity.y) * self.COR
                    if bounce > 1:
                        self.velocity.y *= -1 * self.COR
                    else:
                        self.velocity.y = 0
                else:
                    self.velocity.y = 0
        #######################################
        if DEBUG:
            print(f"Rect Y: {self.rect.y}")
        #######################################

    def SetVelocity(self, vx, vy):
        self.velocity = Vec2(vx, vy)

    def SetVelocityVec2(self, v2):
        self.velocity = v2

    def AddForce(self, source, name, force):
        if type(name) != str:
            raise TypeError("Name must be of type String")
        self.forces.AddForce(source, name, force)

    def RemoveForce(self, source, name):
        self.forces.RemoveForce(source, name)

    def SetWeightless(self, state):
        self.weightless = state

    def GetAngleVec(self):
        return self.angleDir

    def PrintForces(self):
        for force in self.forces:
            print(f"{force}: {str(self.forces[force])}")
        print(f"Resultant force: {self.rForce}")

class Player(PhysObject):
    def __init__(self, pos, image, mass):
        super().__init__(pos, image, mass, PLAYER_DRAG_COEFFICIENT)

def getCameraTrack(pos, lpos, lwidth , lheight):

    x, y = pos.x, pos.y
    swidth, sheight = WINDOW_SIZE
    halfw, halfh = swidth / 2, sheight / 2
    maxWidthOffset = lwidth - swidth
    maxHeightOffset = lheight - sheight
    newlpos = list(lpos)

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


objects = [PhysObject((100, 100), ball_image, 60, SPHERE_DRAG_COEFFICIENT, True, 0.35)]

player = Player((50, 100), player_image, 50)

world = [WorldCollider(pygame.Rect(0, 474, 1279, 720 - 474))]

prev_time = time.time()

player.SetWeightless(False)

ball = objects[0]

lPos = [0, 0]

while True:
    clock.tick()
    now = time.time()
    dt = now - prev_time
    prev_time = now

    oldLPos = lPos
    lPos = getCameraTrack(player.GetPos(), lPos, background_image.get_size()[0], background_image.get_size()[1])

    # move game objects accordingly with the level
    diff = list(numpy.subtract(lPos, oldLPos)) # convert the numpy array to a regular list
    player.SetPos(player.GetPos() + Vec2(diff)) # PhysObjects can be moved via vector addition
    for object in objects:
        object.SetPos(object.GetPos() + Vec2(diff))
    for wc in world: # Worldcolliders are tracked by rects only, so use numpy list subtraction
        wc.Move(diff)

    screen.blit(background_image, tuple(lPos))

    font = pygame.font.Font(None, 30)
    render_fps = font.render(str(int(clock.get_fps())), True, WHITE)
    screen.blit(render_fps, (0, 0))
    render_mousepos = font.render(str(pygame.mouse.get_pos()), True, WHITE)
    screen.blit(render_mousepos, (500, 0))

    colliders = world + objects # Everything the player can collide with

    player.Update(colliders, dt)
    player.Draw(screen)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]:
        player.Rotate(1, colliders)
    if keys[pygame.K_LEFT]:
        player.Rotate(-1, colliders)
    if keys[pygame.K_SPACE]:
        base = Vec2(0, 1000)
        rads = player.angle * RAD
        base.x, base.y = (base.x * math.cos(rads)) - (base.y * math.sin(rads)),\
                 -((base.x * math.sin(rads)) + (base.y * math.cos(rads)))
        player.AddForce(player, "Drive", base)
    elif keys[pygame.K_LSHIFT]:
        base = Vec2(0, 1000)
        rads = player.angle * RAD
        base.x, base.y = -((base.x * math.cos(rads)) - (base.y * math.sin(rads))),\
                 (base.x * math.sin(rads)) + (base.y * math.cos(rads))
        player.AddForce(player, "Drive", base)

    if keys[pygame.K_d]:
        ball.Rotate(1, world + [x for x in objects if x != object])
    if keys[pygame.K_a]:
          ball.Rotate(-1, world + [x for x in objects if x != object])
    if keys[pygame.K_j]:
        ball.AddForce(ball, "Drive", Vec2(1000, 0))
    elif keys[pygame.K_h]:
        ball.AddForce(ball, "Drive", Vec2(-1000, 0))

    if keys[pygame.K_MINUS]:
        lPos[0] = lPos[0] - 1
    elif keys[pygame.K_EQUALS]:
        lPos[0] = lPos[0] + 1

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                player.RemoveForce(player, "Drive")
            if event.key == pygame.K_LSHIFT:
                player.RemoveForce(player, "Drive")
            if event.key == pygame.K_j:
                ball.RemoveForce(ball, "Drive")
            if event.key == pygame.K_h:
                ball.RemoveForce(ball, "Drive")

    newcolliders = [x for x in world]
    newcolliders.append(player)
    for object in objects:
        object.Update(newcolliders + [x for x in objects if x != object], dt)
        object.Draw(screen)


    pygame.display.update()
    clock.tick(FPS)
