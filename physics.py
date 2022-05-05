import pygame, time, numpy, math, sys, copy, random

clock = pygame.time.Clock()

from pygame.locals import *
from constants import *
pygame.init()

pygame.display.set_caption("Physics")
tinyFont = pygame.font.Font(UNISPACE, 9)

class Material:
    def __init__(self, static, kinetic):
        self.static = static
        self.kinetic = kinetic

MATERIALS = {
    "Asphalt": Material(0.9, 0.65),
    "Steel": Material(0.21, 0.133)
}

def trace(source, dir, target, LEVEL_SIZE, detailed=False):
    """
    Traces a straight line from a source in a direction (unit vector) and checks for a hit with another object

    :param source: A source point or object
    :param dir: Normalized vector representing direction of the ray
    :type dir: Vec2
    :param target: What to test for ray collision on
    :param LEVEL_SIZE: The size of the level in pixels/coordinates
    :type LEVEL_SIZE: tuple
    :param detailed: Detailed info about the hit
    :return: Whether a hit was registered
    """
    if not isinstance(source, Vec2):
        source = source.GetPos()
    if not isinstance(target, pygame.Rect) and target is not None:
        target = target.GetRect()
    width, height = WINDOW_SIZE
    xDir = int(identity(dir).x)
    end_pos = (0, 0)
    if xDir != 0: # If the line is not completely vertical; has a gradient
        gradient = dir.y / dir.x # dy/dx
        bounds = [int(source.x), LEVEL_SIZE[0] if xDir == 1 else -LEVEL_SIZE[0]] # How far we should draw the line along the x-axis; always an overestimate
        for x in range(bounds[0], bounds[1], xDir): # Increment along the axis axis by an amount equal to the gradient
            y = x * gradient + source.y # y = mx + c ; c == source.y because the line is transformed an amount up the y axis by source.y

            if DEBUG and x == bounds[1] - xDir:
                end_pos = (x, int(y))
                pygame.draw.aaline(screen, RED, (source.x, source.y), end_pos)
            if target is not None:
                if target.collidepoint(x, y):
                    return True
    else: # If the line is completely vertical; has no gradient
        yDir = int(identity(dir).y)
        bounds = [int(source.y), LEVEL_SIZE[1] if yDir == 1 else -LEVEL_SIZE[1]]
        for y in range(bounds[0], bounds[1], yDir):
            # vertical line given by x=k, where k is source.x
            if DEBUG and y == bounds[1] - yDir:
                end_pos = (source.x, y)
                pygame.draw.aaline(screen, RED, (source.x, source.y), end_pos)
            if target is not None:
                if target.collidepoint(source.x, y):
                    return True
    return False


def coltest(rect, colliders):
    """
    Test collisions between a single object and a list of others

    :param rect: Rect/Object
    :param colliders: List of rects/objects
    :return: A list of all the objects/rects from colliders that 'rect' collided with
    """
    hit_list = []
    for collider in colliders:
        if rect.colliderect(collider.GetRect()):
            hit_list.append(collider)
    return hit_list

def touching(obj1, obj2):
    """
    Test for edge collisions, and determine which sides are involved.

    :param obj1: Object 1
    :param obj2: Object 2
    :return: The side of obj1 which obj2 is touching, or False.
    """
    rect1, rect2 = obj1.GetRect(), obj2.GetRect()

    # Ensuring rects are in the correct position relative to eachother to be able to touch:
    checky = (rect2.top <= rect1.bottom and rect2.bottom >= rect1.top)
    checkx = (rect2.left <= rect1.right and rect2.right >= rect1.left)

    if rect1.left == rect2.right and checky:
        return "left"
    if rect1.right == rect2.left and checky:
        return "right"
    if rect1.top == rect2.bottom and checkx:
        return "top"
    if rect1.bottom == rect2.top and checkx:
        return "bottom"
    return False

def touchingany(ent, colliders):
    """
    Same as touching, but for several objects.

    :param ent: Any object
    :param colliders: List of other objects
    :return: A list of tuple pairs with objects and the side which the ent is touching
    """
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
    """Returns the normalised version of the vector or number that is input. E.g: (-500, 0) becomes (-1,0)"""
    if isinstance(n, Vec2):
        return n.noErrorDiv(abs(n))
    if n != 0:
        return n / abs(n)
    else:
        return n

def textRender(font, pos, text, colour, center=True):
    rendered = font.render(text, True, colour)
    rect = rendered.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    screen.blit(rendered, rect)

class Vec2:
    def __init__(self, *args):
        if len(args) == 1 and (isinstance(args[0], tuple) or isinstance(args[0], list)):
            self.x, self.y = args[0]
        elif len(args) == 2:
            self.x, self.y = args[0], args[1]
    def __abs__(self):
        return Vec2(abs(self.x), abs(self.y))
    def __add__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x + n.x, self.y + n.y)
        return Vec2(self.x + n, self.y + n)
    def __radd__(self, n):
        return self + n
    def __sub__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x - n.x, self.y - n.y)
        return Vec2(self.x - n, self.y - n)
    def __eq__(self, v2):
        return self.x == v2.x and self.y == v2.y
    def __mul__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x * n.x, self.y * n.y)
        return Vec2(self.x * n, self.y * n)
    def __rmul__(self, n):
        return self * n
    def __truediv__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x / n.x, self.y / n.y)
        return Vec2(self.x / n, self.y / n)
    def __floordiv__(self, n):
        if isinstance(n, Vec2):
            return Vec2(self.x // n.x, self.y // n.y)
        return Vec2(self.x // n, self.y // n)
    def __pow__(self, pow):
        return Vec2(self.x ** pow, self.y ** pow)
    def __str__(self):
        return f"{str(self.x)}, {str(self.y)}"
    def __round__(self, n):
        return Vec2(round(self.x, n), round(self.y, n))
    def __iter__(self):
        yield self.x
        yield self.y
    def Integer(self):
        return Vec2(int(self.x), int(self.y))
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
        return self.noErrorDiv(mag)
    def Inverse(self):
        return self * -1
    def noErrorDiv(self, n):
        new = Vec2(0, 0)
        if isinstance(n, Vec2):
            new.x = self.x / n.x if n.x != 0 else 0
            new.y = self.y / n.y if n.y != 0 else 0
            return new
        else:
            new = self / n if n != 0 else 0
            return new


dir = {"left" : Vec2(-1, 0),
       "top" : Vec2(0, -1),
       "right" : Vec2(1, 0),
       "bottom" : Vec2(0, 1)}


class Force(Vec2):
    def __init__(self, source, name, *args):
        self.source = source
        self.name = name
        if len(args) == 1: # in case the components are passed as a tuple/list
            self.x, self.y = args[0].x, args[0].y
        if len(args) == 2: # if the components are passed seperately
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
    def Update(self, constants, colliders, dt):
        parent = self.parent
        v = parent.velocity

        gravity, airdensity = constants["gravity"], constants["airdensity"]

        touching = touchingany(parent, colliders)
        touchingEnts = [x[0] for x in touching]

        rForce = self.GetResultantNOF()  # Alternative rForce where we ignore drag forces

        ## REMOVE REDUNDANT FORCES FROM ENTITIES NOT IN CONTACT/NOT OURSELF OR NOT APPLICABLE ##
        for i, force in enumerate(self.forces):
            # Contact Check (applies to any force)
            if force.source not in touchingEnts and force.source != self.parent and force.name != "Wind":
                self.forces.pop(i)
                continue

            # Friction Check
            if force.name == "FrictionX":
                if v.x == 0 and rForce.x == 0:
                    self.forces.pop(i)
                    continue
            if force.name == "FrictionY":
                if v.y == 0 and rForce.y == 0:
                    self.forces.pop(i)
                    continue


        ## ADD WEIGHT FORCE IF IT DOESN'T EXIST ##
        if not parent.weightless and GRAVITYON:
            self.AddForce(parent, "Weight", 0, parent.mass * gravity)
        if not GRAVITYON or parent.weightless:
            self.RemoveForce(parent, "Weight")


        ## ADD NORMAL FORCE IF THERE IS AN OPPOSING FORCE ##
        for result in touching:
            ent, side = result
            if isinstance(ent, WorldCollider):
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
            dragmag = v.GetSqrMag() * 0.5 * airdensity * parent.Cd * A
            drag = v.GetNormalized().Inverse() * dragmag  # Turn drag magnitude into an opposite-facing vector to velocity
            parent.AddForce(parent, "Air Resistance", drag)

        ## ADD FRICTION ##
        for result in touching:
            ent, side = result
            if isinstance(ent, WorldCollider):
                if self.GetForce(ent, "ReactionY") or self.GetForce(ent, "ReactionX"):
                    N = 0
                    if side == "top" or side == "bottom":
                        force = self.GetForce(ent, "ReactionY")
                        if force is not None:
                            N = abs(force.y)
                    else:
                        force = self.GetForce(ent, "ReactionX")
                        if force is not None:
                            N = abs(force.x)

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

        parent.acceleration = self.rForce / parent.mass # a = F/m
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
        if DEBUG and isinstance(self.parent, Player):
            for force in self.forces:
                print(f"    {force.name}: {force} -- SOURCE: {force.source}")

        #########################################

class WorldCollider:
    def __init__(self, rect, material="Asphalt"):
        self.rect = rect
        self.pos = Vec2(rect.topleft)
        self.material = MATERIALS[material]
    def DrawDebug(self):
        pygame.draw.rect(screen, RED, self.rect, 1)
    def GetRect(self):
        return self.rect
    def GetPos(self):
        return self.pos
    def Move(self, delta):
        self.pos += delta
        self.rect.topleft = tuple(self.pos)
    def GetMaterial(self):
        return self.material
    def GetMuStatic(self):
        return self.material.static
    def GetMuKinetic(self):
        return self.material.kinetic

class PhysObject:
    def __init__(self, pos, image, mass, Cd=0.5, COR=0):
        """
        :param Vec2 pos:
        :param string image:
        :param float mass:
        :param float Cd:
        :param float COR:
        """
        self.pos = Vec2(pos[0], pos[1])
        self.angle = 0
        self.angleDir = Vec2(math.cos((90 + self.angle) * RAD), -math.sin((90 - self.angle) * RAD)).GetNormalized()
        self.image_clean, self.image = image, image
        self.halfheight = self.image_clean.get_height() / 2
        self.halfwidth = self.image_clean.get_width() / 2
        self.rect = self.image.get_rect(center=(pos[0], pos[1]))
        self.mass = mass
        self.Cd = Cd
        self.COR = COR
        self.weightless = False
        self.forces = ForceManager(self)
        self.rForce = Vec2(0, 0)
        self.acceleration = Vec2(0, 0)
        self.velocity = Vec2(0, 0)
        self.momentum = Vec2(0, 0)
        self.detailsMode = False
    def DrawDetails(self, surface):
        details = [
            f"Mass: {self.mass} kg",
            f"Velocity: ({str(round(self.velocity, 1))}) m/s",
            f"Acceleration: ({str(round(self.acceleration, 1))}) m/s²",
            f"Resultant Force: ({str(round(self.rForce, 1))}) N",
            "Forces:"
        ]
        for force in self.forces.forces:
            details.append(f"   {force.name}: ({str(round(force, 1))}) N")
        if isinstance(self, Player):
            details = [f"Engine Drive: {self.thrust} N"] + details
        fontSize = tinyFont.size("a")
        rectHeight = (len(details) * fontSize[1]) + 10
        rectWidth = 230
        detailsRect = pygame.Rect(0, 0, rectWidth, rectHeight)
        detailsRect.left = self.rect.right
        detailsRect.centery = self.rect.centery
        pygame.draw.rect(surface, NEARLYBLACK, detailsRect, 0, 7)
        pygame.draw.rect(surface, BLACK, detailsRect, 3, 7)
        for i, detail in enumerate(details):
            textRender(tinyFont, (detailsRect.topleft[0] + 8, detailsRect.topleft[1] + 4 + (fontSize[1] * i)), detail,
                       WHITE, False)
    def Draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.detailsMode:
            self.DrawDetails(surface)
        if DEBUG:
            pygame.draw.rect(surface, RED, self.rect, 1)
            image_rect = self.image.get_rect()
            image_rect.center = self.rect.center
            pygame.draw.rect(surface, YELLOW, image_rect, 1)
            pygame.draw.circle(surface, RED, self.rect.center, 1)
            if isinstance(self, Player):
                pygame.draw.circle(surface, RED, tuple(self.engine), 1)
    def GetPos(self):
        return self.pos
    def GetCentre(self):
        return self.GetRect().center
    def SetPos(self, p):
        self.pos = p
    def GetRect(self):
        return self.rect
    def Rotate(self, scale, colliders, dt):
        if len(touchingany(self, colliders)) == 0:
            old_rect = copy.deepcopy(self.rect)
            scale *= -1 # We want to interpret + rotation as clockwise
            self.angle += PLAYER_ROTATION_SPEED * scale * dt
            rotated_image = pygame.transform.rotate(self.image_clean, self.angle)
            self.image = rotated_image
            self.rect = self.image.get_rect(center=old_rect.center)
            self.angleDir = Vec2(math.cos((90 + self.angle) * RAD), -math.sin((90 - self.angle) * RAD)).GetNormalized()
    def Update(self, constants, colliders, dt):
        if DEBUG and isinstance(self, Player):
            print(type(self))

        self.engine = self.GetPos() + Vec2(self.halfheight * math.sin(self.angle * RAD), self.halfheight * math.cos(self.angle * RAD))

        self.forces.Update(constants, colliders, dt)
        self.velocity += self.acceleration * dt

        if round(self.velocity.x, 1) == 0 and identity(self.velocity.x) != identity(self.rForce.x): # If velocity is basically 0, and velocity is opposing the direction of
            self.velocity.x = 0                                                                        # resultant force, set this velocity to exactly 0.
        if round(self.velocity.y, 1) == 0 and identity(self.velocity.y) != identity(self.rForce.y):
            self.velocity.y = 0

        self.momentum = self.velocity * self.mass

        ##################################################
        if DEBUG and isinstance(self, Player):
            print(f"Pos: {str(self.pos)}")
            print(f"Resultant Force: {str(self.rForce)}")
            print(f"Acceleration: {str(self.acceleration)}")
            print(f"Velocity: {str(self.velocity)}")
            print(f"Momentum: {str(self.momentum)}")
            print(f"Angle: {str(self.angle)}")
            print(f"Angle Vector: {str(self.angleDir)}")

        ##################################################

        tempcolliders = [x for x in colliders if isinstance(x, WorldCollider)]
        delta = self.velocity * dt * METRE

        colData = CollisionHandler.SafeMove(self, tempcolliders, delta)

        if colData["x"]:
            if isinstance(self, Player) and not (isinstance(colData["objectX"], PhysObject) or
                                                 isinstance(colData["objectX"], Objective)):
                if abs(self.velocity.x) >= 10:
                    self.collisions += 1
            if self.COR > 0:
                bounce = abs(self.velocity.x) * self.COR
                if bounce > 1:
                    self.velocity.x *= -1 * self.COR
                else:
                    self.velocity.x = 0
            else:
                self.velocity.x = 0

        if colData["y"]:
            if isinstance(self, Player) and not (isinstance(colData["objectY"], PhysObject) or
                                                 isinstance(colData["objectY"], Objective)):
                if abs(self.velocity.y) >= 10:
                    self.collisions += 1
            if self.COR > 0:
                bounce = abs(self.velocity.y) * self.COR
                if bounce > 1:
                    self.velocity.y *= -1 * self.COR
                else:
                    self.velocity.y = 0
            else:
                self.velocity.y = 0
    def SetVelocity(self, vx, vy):
        self.velocity = Vec2(vx, vy)
    def SetVelocityVec2(self, v2):
        self.velocity = v2
    def GetVelocity(self):
        return self.velocity
    def AddForce(self, source, name, force):
        """
        :param source:
        :param name:
        :param force:
        :return:
        """
        if type(name) != str:
            raise TypeError("Name must be of type String")
        self.forces.AddForce(source, name, force)
    def RemoveForce(self, source, name):
        self.forces.RemoveForce(source, name)
    def GetResultantForce(self):
        return self.rForce
    def GetResultantNOF(self):
        return self.forces.GetResultantNOF()
    def SetWeightless(self, state):
        self.weightless = state
    def GetAngleVec(self):
        return self.angleDir
    def PrintForces(self):
        for force in self.forces:
            print(f"{force}: {str(self.forces[force])}")
        print(f"Resultant force: {self.rForce}")
    def ToggleDetails(self):
        self.detailsMode = True if not self.detailsMode else False

class Player(PhysObject):
    def __init__(self, pos, image, mass, fuel, thrust, weightlessfuel=False):
        """
        :param float fuel:
        :param float thrust:
        :param bool weightlessfuel:
        """
        super().__init__(pos, image, mass, PLAYER_DRAG_COEFFICIENT, 0.2)
        self.fuel, self.tank = fuel, fuel
        self.weightlessfuel = weightlessfuel
        self.bodymass = mass
        self.mass = self.bodymass + self.fuel if not weightlessfuel else self.bodymass
        self.thrust = thrust
        self.collisions = 0
    def Update(self, constants, colliders, dt):
        if not self.weightlessfuel:
            self.mass = self.bodymass + self.fuel
        super().Update(constants, colliders, dt)
        if self.fuel <= 1:
            self.RemoveForce(self, "Drive")
    def Thrust(self, particleHandler, reverse=False):
        if self.fuel >= 1:
            base = Vec2(0, self.thrust)
            rads = self.angle * RAD
            base.x, base.y = (base.x * math.cos(rads)) - (base.y * math.sin(rads)), \
                             -((base.x * math.sin(rads)) + (base.y * math.cos(rads)))
            if reverse:
                base *= -1
            self.AddForce(self, "Drive", base)
            particleHandler.CreateEngineParticles(self, base)
            self.fuel -= 1

class KeyObject(PhysObject):
    def __init__(self, pos, image, mass, colour, Cd=0.5, COR=0):
        super().__init__(pos, image, mass, Cd, COR)
        self.colour = colour
        self.lastEmission = time.time()

class Collision:
    def __init__(self, object, collider):
        self.object = object
        self.collider = collider
        self.resolved = False
    def __eq__(self, other):
        return self.object == other.object and self.collider == other.collider or \
               self.object == other.collider and self.collider == other.object

    @staticmethod
    def pushing(obj1, obj2, level_size):
        """
        :param obj1:
        :type obj1: PhysObject
        :param obj2:
        :type obj2: PhysObject
        :return: Whether object 1's resultant force and velocity direction is into object 2
        """
        if obj1.GetResultantForce() != Vec2(0, 0) and obj1.GetVelocity() != Vec2(0, 0):
            source = Vec2(obj1.GetCentre())
            return trace(source, obj1.GetResultantForce().GetNormalized(), obj2, level_size) and \
            trace(source, obj1.GetVelocity().GetNormalized(), obj2, level_size)
        else:
            return False

    def Resolve(self):
        obj1 = self.object
        obj2 = self.collider
        pTotal = obj1.momentum + obj2.momentum
        finalObj1V = obj2.velocity - obj1.velocity # + finalObj2V
        pTotal = pTotal - (finalObj1V * obj1.mass)
        finalObj2V = pTotal / (obj1.mass + obj2.mass)
        finalObj1V = finalObj1V + finalObj2V
        obj1.SetVelocityVec2(finalObj1V)
        obj2.SetVelocityVec2(finalObj2V)
        self.resolved = True

    def CheckOverlap(self):
        return self.object.GetRect().colliderect(self.collider.GetRect()) or touching(self.object, self.collider)
    def ResolveOverlap(self, level_size):
        obj1, obj2 = self.object, self.collider

        if Collision.pushing(obj1, obj2, level_size):
            obj2.AddForce(obj1, "Push", obj1.GetResultantNOF())
            obj1.AddForce(obj2, "Reaction", obj1.GetResultantNOF())
        else:
            obj2.RemoveForce(obj1, "Push")
            obj1.RemoveForce(obj2, "Reaction")

        if Collision.pushing(obj2, obj1, level_size):
            obj1.AddForce(obj2, "Push", obj2.GetResultantNOF())
            obj2.AddForce(obj1, "Reaction", obj2.GetResultantNOF())
        else:
            obj1.RemoveForce(obj2, "Push")
            obj2.RemoveForce(obj1, "Reaction")
    def PreRemoval(self):
        obj1, obj2 = self.object, self.collider
        obj1.RemoveForce(obj2, "Push")
        obj2.RemoveForce(obj1, "Reaction")
        obj2.RemoveForce(obj1, "Push")
        obj1.RemoveForce(obj2, "Reaction")

class CollisionHandler:
    def __init__(self, level_size):
        self.collisions = []
        self.level_size = level_size
    def ColScan(self, world):
        for object in world:
            otherObjects = [x for x in world if x != object]  # All the other objects in the world
            collisionIndex = object.GetRect().collidelistall(otherObjects)  # Get the indexes for every object we are colliding with
            colliders = [otherObjects[x] for x in collisionIndex]  # Create a list of objects by their indexes
            for collider in colliders:
                collision = Collision(object, collider)
                if collision not in self.collisions:
                    self.collisions.append(collision)
    def Update(self, world):
        self.ColScan(world)
        for i, collision in enumerate(self.collisions):
            if not collision.resolved:
                collision.Resolve()
            else:
                if collision.CheckOverlap():
                   collision.ResolveOverlap(self.level_size)
                if not collision.CheckOverlap():
                    collision.PreRemoval()
                    self.collisions.pop(i)

    @staticmethod
    def SafeMove(object, colliders, delta):
        """
        Conducts movement with respect to collisions that occur with any objects in the 'colliders' list.

        :param object: Subject of movement
        :param colliders: All other collidable objects
        :type colliders: list
        :param delta: How much the subject is desired to be moved by
        :type delta: Vec2
        :return: Dictionary containing which sides were hit and the objects involved in them
        """

        returnVals = {"x": False,
                      "y": False,
                      "objectX": None,
                      "objectY": None}

        ## HANDLE X MOVEMENT ##
        oldRect = copy.deepcopy(object.GetRect())
        object.pos.x += delta.x
        if isinstance(object, WorldCollider):
            object.rect.left = object.pos.x
        else:
            object.rect.centerx = object.pos.x
        colliders = [x for x in colliders if object != x]
        hit_list = coltest(object.rect, colliders)


        for entity in hit_list:
            if delta.x > 0 and oldRect.right <= entity.rect.left:
                object.rect.right = entity.GetRect().left
                object.pos = Vec2(object.rect.center) # object's internal pos attribute must be adjusted accordingly

            elif delta.x < 0 and oldRect.left >= entity.rect.right:
                object.rect.left = entity.GetRect().right
                object.pos = Vec2(object.rect.center)

            returnVals["x"] = True
            returnVals["objectX"] = entity

        ###########################################

        oldRect = copy.deepcopy(object.GetRect())
        object.pos.y += delta.y
        if isinstance(object, WorldCollider):
            object.rect.top = object.pos.y
        else:
            object.rect.centery = object.pos.y
        hit_list = coltest(object.rect, colliders)

        for entity in hit_list:
                if delta.y > 0 and oldRect.bottom <= entity.rect.top:
                    object.rect.bottom = entity.GetRect().top
                    object.pos = Vec2(object.rect.center)

                elif delta.y < 0 and oldRect.top >= entity.rect.bottom:
                    object.rect.top = entity.GetRect().bottom
                    object.pos = Vec2(object.rect.center)

                returnVals["y"] = True
                returnVals["objectY"] = entity

        return returnVals


def lINTerp(lb, ub, fraction):
    interval = (abs(ub - lb) * fraction)
    if lb < ub:
        return int(lb + interval)
    else:
        return int(lb - interval)

class Particle:
    def __init__(self, pos, velocity, timer, weightless=False, colour=WHITE, radius=1, colSim=False, parent=None):
        self.pos = pos
        self.velocity = velocity
        self.elapsed = 0
        self.timer = timer
        self.rect = pygame.Rect(self.pos.x - radius, self.pos.y - radius, radius*2, radius*2)
        self.weightless = weightless
        self.colour = colour
        self.radius = radius
        self.acceleration = Vec2(0, 0)
        self.colSim = colSim
        self.parent = parent
    def Update(self, dt, gravity, colliders=None):
        world = [x for x in colliders]
        self.elapsed += dt
        self.acceleration = Vec2(0, gravity if GRAVITYON and not self.weightless else 0)
        self.velocity += self.acceleration * dt
        if self.colSim:
            if self.parent is not None and self.parent in world:
                world.remove(self.parent)
            touch = CollisionHandler.SafeMove(self, world, self.velocity * dt * METRE) # returns dictionary with sides that were touched
            if touch["x"]:
                if isinstance(self, EngineParticle):
                    self.velocity.x *= -0.8
                else:
                    self.velocity.x *= -0.01
            if touch["y"]:
                if isinstance(self, EngineParticle):
                    self.velocity.y *= -0.8
                else:
                    self.velocity.y *= -0.01
        else:
            self.pos += self.velocity * dt * METRE
        self.rect.center = tuple(self.pos)
    def SetPos(self, pos):
        self.pos = pos
    def GetPos(self):
        return self.pos
    def Draw(self, screen):
        pygame.draw.circle(screen, self.colour, tuple(self.pos), self.radius)
        if DEBUG:
            pygame.draw.rect(screen, RED, self.rect, 1)
    def GetRect(self):
        return self.rect


class EngineParticle(Particle):
    def __init__(self, pos, velocity, timer, player):
        super().__init__(pos, velocity, timer, colSim=True, parent=player)
        self.colour = [255, 174, 0, 255]
        self.radius = 2
    def Update(self, dt, gravity, colliders):
        super().Update(dt, gravity, colliders)
        if self.elapsed < self.timer:
            frac = self.elapsed / self.timer # How white the particle should be
            self.colour[1] = lINTerp(174, 255, frac)
            self.colour[2] = lINTerp(0, 255, frac)
            self.colour[3] = lINTerp(0, 255, frac)
            self.radius = lINTerp(2, 5, frac)


class ParticleHandler:
    def __init__(self):
        self.particles = []
    def Update(self, screen, world, gravity, dt):
        for i, particle in enumerate(self.particles):
            particle.Update(dt, gravity, world)
            if particle.elapsed >= particle.timer != 0: # if particle.timer == 0 it is an infinite particle; will not expire
                self.particles.pop(i)

        for particle in self.particles:
            particle.Draw(screen)

        for obj in world:
            now = time.time()
            if isinstance(obj, KeyObject) or isinstance(obj, Objective):
                if now - obj.lastEmission >= 0.5: # Map objects emit particles every ~0.5 seconds
                    self.Emit(obj, obj.colour, 3, Vec2(random.uniform(-1, 1), random.uniform(-5, -2)), True, False, obj) # Emit particles generally in the upwards direction
                    obj.lastEmission = now
            if type(obj) == AirStream:
                if now - obj.lastEmission >= 0.1: # Airstream particles are released at 0.1 second intervals
                    velocity = obj.GetForce().GetNormalized() * 30
                    self.Emit(obj, WHITE, 4, velocity, True, True, obj)
                    obj.lastEmission = now

    def Emit(self, obj, colour, life, velocity, weightless=False, colSim=False, parent=None):
        pos, rect = tuple(obj.GetPos()), obj.GetRect()
        pos = rect.center if pos != rect.center else pos
        x = random.randint(int(pos[0] - (rect.width / 2)), int(pos[0] + (rect.width / 2)))
        y = random.randint(int(pos[1] - (rect.height / 2)), int(pos[1] + (rect.height / 2)))

        self.Add(Particle(Vec2(x, y), velocity, life, weightless, colour, 2, colSim, parent))

    def Add(self, particle):
        self.particles.append(particle)
    def CreateEngineParticles(self, ship, drive):
        for i in range(0, 10):
            x, y = tuple(ship.engine) # Starting pos is the engine
            uv = drive.Inverse().GetNormalized() + Vec2(random.uniform(-1, 1), 0)
            self.Add(EngineParticle(ship.engine, uv, random.uniform(0.5, 0.8), ship))

class Objective(WorldCollider):
    def __init__(self, pos, width, height, material="Asphalt"):
        super().__init__(pygame.Rect(pos.x, pos.y, width, height), material)
        self.original, self.colour = GREY, GREY
        self.complete = False
        self.lastEmission = time.time()
    def Update(self, triggers):
        for trigger in triggers:
            if trigger.GetRect().colliderect(self.rect) or touching(trigger, self):
                self.colour = GREEN
                self.complete = True
                return True
        self.colour = self.original
        self.complete = False
        return False
    def Draw(self, screen):
        pygame.draw.rect(screen, self.colour, self.rect)
    def GetRect(self):
        return self.rect

class PlayerObjective(Objective):
    def __init__(self, pos, width, height):
        super().__init__(pos, width, height)
        self.original, self.colour = YELLOW, YELLOW

class PhysObjective(Objective):
    def __init__(self, pos, width, height):
        super().__init__(pos, width, height)
        self.original, self.colour = PINK, PINK

class Obstacle(WorldCollider):
    def __init__(self, pos, width, height, player):
        super().__init__(pygame.Rect(pos.x, pos.y, width, height), material="Asphalt")
        self.colour = RED
        self.player = player
    def Update(self, player):
        if self.player.GetRect().colliderect(self.rect) or touching(self.player, self):
            print("GAME OVER!!!!!")
            return True
        return False
    def Draw(self, screen):
        pygame.draw.rect(screen, self.colour, self.rect)
    def GetRect(self):
        return self.rect

class AirStream(WorldCollider):
    def __init__(self, pos, width, height, streamWidth, streamHeight, force):
        super().__init__(pygame.Rect(pos.x, pos.y, width, height), material="Steel")
        self.colour = STEEL
        self.force = force
        self.lastEmission = time.time()
        self.oldPos = copy.deepcopy(self.pos)

        if streamWidth != 0:
            if streamWidth > 0: # If its a horizontal airstream
                self.streamRect = pygame.Rect(*self.rect.topright, streamWidth, height) # Going to the right
            else:
                self.streamRect = pygame.Rect(pos.x + streamWidth, pos.y, -streamWidth, height) # Going to the left
        else:
            if streamHeight > 0: # If its a vertical airstream
                self.streamRect = pygame.Rect(*self.rect.bottomleft, width, streamHeight) # Going down
            else:
                self.streamRect = pygame.Rect(pos.x, pos.y + streamHeight, width, -streamHeight) # Going up

    def Update(self, objects):
        for obj in objects:
            if self.streamRect.contains(obj.GetRect()) or self.streamRect.colliderect(obj.GetRect()): # If the object is within the airstream's zone
                obj.AddForce(self, "Wind", self.force)
            else:
                obj.RemoveForce(self, "Wind")

        if self.pos - self.oldPos != Vec2(0, 0): # check if the source was moved and move the airstream accordingly
            self.streamRect.topleft = tuple(Vec2(self.streamRect.topleft) + (self.pos - self.oldPos))
            self.oldPos = copy.deepcopy(self.pos)
    def Draw(self, screen):
        pygame.draw.rect(screen, self.colour, self.rect)
        if DEBUG:
            pygame.draw.rect(screen, RED, self.streamRect, 1)
    def GetForce(self):
        return self.force


