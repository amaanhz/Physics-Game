import pygame, time, numpy, math, sys, copy, random

clock = pygame.time.Clock()

from pygame.locals import *
from constants import *
pygame.init()

pygame.display.set_caption("Physics")

class Material:
    def __init__(self, static, kinetic, cor):
        self.static = static
        self.kinetic = kinetic
        self.bounceModifier = cor

MATERIALS = {
    "Asphalt": Material(0.9, 0.65, 0.8)
}

def trace(source, dir, target, LEVEL_SIZE, detailed=False):
    """
    :param source: A source point or object
    :param dir: Normalized vector representing direction of the ray
    :type dir: Vec2
    :param target: What to test for ray collision on
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
    if xDir != 0:
        gradient = dir.y / dir.x
        bounds = [int(source.x), LEVEL_SIZE[0] if xDir == 1 else -LEVEL_SIZE[0]]
        for x in range(bounds[0], bounds[1], xDir):
            y = x * gradient + source.y

            if DEBUG and x == bounds[1] - xDir:
                end_pos = (x, int(y))
                pygame.draw.aaline(screen, RED, (source.x, source.y), end_pos)
            if target is not None:
                if target.collidepoint(x, y):
                    return True
    else:
        yDir = int(identity(dir).y)
        bounds = [int(source.y), LEVEL_SIZE[1] if yDir == 1 else -LEVEL_SIZE[1]]
        for y in range(bounds[0], bounds[1], yDir):

            if DEBUG and y == bounds[1] - yDir:
                end_pos = (source.x, y)
                pygame.draw.aaline(screen, RED, (source.x, source.y), end_pos)
            if target is not None:
                if target.collidepoint(source.x, y):
                    return True
    return False


def coltest(rect, colliders):
    hit_list = []
    for collider in colliders:
        if rect.colliderect(collider.GetRect()):
            hit_list.append(collider)
    return hit_list

def touching(obj1, obj2):
    """
    :param obj1: Object 1
    :param obj2: Object 2
    :return: The side of obj1 which obj2 is touching, or False.
    """
    rect1, rect2 = obj1.GetRect(), obj2.GetRect()
    checky = (rect2.top <= rect1.bottom and rect2.bottom >= rect1.top)
    checkx = (rect2.left <= rect1.right and rect2.right >= rect1.left)
    if rect1.left == rect2.right and checky:
        return "left"
    if rect1.right == rect2.left and checkx:
        return "right"
    if rect1.top == rect2.bottom and checky:
        return "top"
    if rect1.bottom == rect2.top and checkx:
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
    """Returns the normalised version of the vector or number that is input. E.g: (-500, 0) becomes (-1,0)"""
    if isinstance(n, Vec2):
        return n.noErrorDiv(abs(n))
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
        if not parent.weightless and not self.GetForce(parent, "Weight") and GRAVITYON:
            self.AddForce(parent, "Weight", 0, parent.mass * GRAVITY)
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
        self.material = MATERIALS[material]
    def DrawDebug(self):
        pygame.draw.rect(screen, RED, self.rect, 1)
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
        self.circular = False
    def Draw(self, surface):
        surface.blit(self.image, self.rect)
        if DEBUG:
            pygame.draw.rect(screen, RED, self.rect, 1)
            image_rect = self.image.get_rect()
            image_rect.center = self.rect.center
            pygame.draw.rect(screen, YELLOW, image_rect, 1)
            pygame.draw.circle(screen, RED, self.rect.center, 1)
            #pygame.draw.circle(screen, RED, tuple(self.GetPos() - (self.GetAngleVec() * (Vec2(self.image.get_size()) / 2))), 1)
            pygame.draw.circle(screen, RED, tuple(self.engine), 1)
    def GetPos(self):
        return self.pos
    def GetCentre(self):
        return self.GetRect().center
    def SetPos(self, p):
        self.pos = p
    def GetRect(self):
        return self.rect
    def Rotate(self, scale, colliders):
        if len(touchingany(self, colliders)) == 0:
            old_rect = copy.deepcopy(self.rect)
            scale *= -1 # We want to interpret + rotation as clockwise
            self.angle += PLAYER_ROTATION_SPEED * scale
            rotated_image = pygame.transform.rotate(self.image_clean, self.angle)
            self.image = rotated_image
            self.rect = self.image.get_rect(center=old_rect.center)
            self.angleDir = Vec2(math.cos((90 + self.angle) * RAD), -math.sin((90 - self.angle) * RAD)).GetNormalized()
    def Update(self, colliders, dt):
        if DEBUG and isinstance(self, Player):
            print(type(self))

        self.engine = self.GetPos() + Vec2(self.halfheight * math.sin(self.angle * RAD), self.halfheight * math.cos(self.angle * RAD))

        self.forces.Update(colliders, dt)
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



        collision_types = {"top": False, "bottom": False, "left": False, "right": False}


        ## HANDLE X MOVEMENT ##
        prevposx = self.pos.x
        self.pos.x += self.velocity.x * dt * METRE
        self.rect.centerx = round(self.pos.x)
        hit_list = coltest(self.rect, colliders)

        for entity in hit_list:
            if isinstance(entity, WorldCollider):
                if self.velocity.x > 0:
                    self.rect.right = entity.GetRect().left
                    self.pos = Vec2(self.rect.center)
                    collision_types["right"] = True

                elif self.velocity.x < 0:
                    self.rect.left = entity.GetRect().right
                    self.pos = Vec2(self.rect.center)
                    collision_types["left"] = True

                if self.COR > 0:
                    bounce = abs(self.velocity.x) * self.COR
                    if bounce > 1:
                        self.velocity.x *= -1 * self.COR
                    else:
                        self.velocity.x = 0
                else:
                    self.velocity.x = 0
        #######################################
        if DEBUG and isinstance(self, Player):
            print(f"Rect X: {self.rect.x}")
        #######################################

        ## HANDLE Y MOVEMENT ##
        prevposy = self.pos.y
        self.pos.y += self.velocity.y * dt * METRE
        self.rect.centery = round(self.pos.y)
        hit_list = coltest(self.rect, colliders)

        for entity in hit_list:
            if isinstance(entity, WorldCollider):
                if self.velocity.y > 0:
                    self.rect.bottom = entity.GetRect().top
                    self.pos = Vec2(self.rect.center)
                    collision_types["bottom"] = True

                elif self.velocity.y < 0:
                    self.rect.top = entity.GetRect().bottom
                    self.pos = Vec2(self.rect.center)
                    collision_types["top"] = True

                if self.COR > 0:
                    bounce = abs(self.velocity.y) * self.COR
                    if bounce > 1:
                        self.velocity.y *= -1 * self.COR
                    else:
                        self.velocity.y = 0
                else:
                    self.velocity.y = 0
        #######################################
        if DEBUG and isinstance(self, Player):
            print(f"Rect Y: {self.rect.y}")
        #######################################
    def SetVelocity(self, vx, vy):
        self.velocity = Vec2(vx, vy)
    def SetVelocityVec2(self, v2):
        self.velocity = v2
    def GetVelocity(self):
        return self.velocity
    def AddForce(self, source, name, force):
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

class Player(PhysObject):
    def __init__(self, pos, image, mass):
        super().__init__(pos, image, mass, PLAYER_DRAG_COEFFICIENT)


class Collision:
    def __init__(self, object, collider):
        self.object = object
        self.collider = collider
        self.resolved = False
        # self.worldCollision = isinstance(self.object, WorldCollider) or isinstance(self.collider, WorldCollider)
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
    # def seperate(self):
    #     obj1, obj2 = self.object, self.collider
    #     v1, v2 = obj1.GetVelocity(), obj2.GetVelocity()
    #     v1Norm, v2Norm = v1.GetNormalized(), v2.GetNormalized()
    #     v1Mag, v2Mag = v1.GetMag(), v2.GetMag()
    #     totalVelocity = v1Mag + v2Mag
    #     v1Perc, v2Perc = v1Mag / totalVelocity if totalVelocity != 0 else 0, v2Mag / totalVelocity if totalVelocity != 0 else 0
    #     obj1Offset, obj2Offset = v1 * v1Perc, v2 * v2Perc
    #     while self.object.GetRect().colliderect(self.collider.GetRect()):
    #         obj1.SetPos(obj1.GetPos() + obj1Offset)
    #         obj2.SetPos(obj2.GetPos() + obj2Offset)

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

        #self.seperate()

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

def lINTerp(lb, ub, fraction):
    return int(((ub - lb) * fraction) + lb)

class Particle:
    def __init__(self, pos, velocity, timer, weightless=False):
        self.pos = pos
        self.velocity = velocity
        self.elapsed = 0
        self.timer = timer
        self.rect = pygame.Rect(self.pos.x - 1, self.pos.y - 1, 2, 2)
        self.weightless = weightless
    def Update(self, dt):
        self.elapsed += dt
        self.acceleration = Vec2(0, GRAVITY if GRAVITYON and not self.weightless else 0)
        self.velocity += self.acceleration * dt
        self.pos += self.velocity * dt
        self.rect.center = tuple(Vec2(self.rect.center) + (self.velocity * dt))
    def SetPos(self, pos):
        self.pos = pos
    def GetPos(self):
        return self.pos

class EngineParticle(Particle):
    def __init__(self, pos, velocity, timer):
        super().__init__(pos, velocity, timer)
        self.colour = [255, 174, 0, 255]
        self.radius = 2
    def Update(self, dt):
        super().Update(dt)
        if self.elapsed < self.timer:
            frac = self.elapsed / self.timer
            self.colour[1] = lINTerp(174, 255, frac)
            self.colour[2] = lINTerp(0, 255, frac)
            self.colour[3] = lINTerp(0, 255, frac)
            self.radius = lINTerp(2, 5, frac)
    def Draw(self):
        pygame.draw.circle(screen, self.colour, tuple(self.pos), self.radius)

class ParticleHandler:
    def __init__(self):
        self.particles = []
    def Update(self, dt):
        for i, particle in enumerate(self.particles):
            particle.Update(dt)
            if particle.elapsed >= particle.timer:
                self.particles.pop(i)
        for particle in self.particles:
            particle.Draw()
    def Add(self, particle, parent=None):
        self.particles.append(particle)
    def CreateEngineParticles(self, ship):
        width, height = ship.image.get_size()
        enginePos = ship.GetPos() - (ship.GetAngleVec() * (height / 2))
        for p in range(0, width):
            pass

class Objective:
    def __init__(self, pos, width, height, trigger):
        self.pos = pos
        self.rect = pygame.Rect(pos[0], pos[1], width, height)
        self.colour = GREY
        self.trigger = trigger
    def Update(self):
        if self.trigger.getRect().colliderect(self.rect):
            return True
        return False
    def Draw(self, screen):
        pygame.draw.rect(screen, self.colour, self.rect)

class PlayerObjective(Objective):
    def __init__(self, pos, width, height, player):
        super.__init__(pos, width, height, player)
        self.colour = GREEN

class PhysObjective(Objective):
    def __init__(self, pos, width, height, obj):
        super.__init__(pos, width, height, obj)
        self.colour = GREEN