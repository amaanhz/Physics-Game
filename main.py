from physics import *

objects = [PhysObject((100, 100), ball_image, 150, SPHERE_DRAG_COEFFICIENT, True, 0.35)]
for i in range(0, 5):
    objects.append(PhysObject((random.randint(0, swidth - ball_image.get_width()), random.randint(0, sheight - ball_image.get_height())), ball_image, 150, SPHERE_DRAG_COEFFICIENT, True, 0.35))
player = Player((50, 100), player_image, 100)

world = [WorldCollider(pygame.Rect(0, 474, 1279, 720 - 474))]
yTop = 0 - (lheight - sheight)
world.append(WorldCollider(pygame.Rect(-1, yTop, 1, lheight)))
world.append(WorldCollider(pygame.Rect(0, yTop - 1, lwidth, 1)))
world.append(WorldCollider(pygame.Rect(lwidth, yTop, 1, lheight)))

ball = objects[0]
player.SetWeightless(False)
ball.SetWeightless(False)
colHandler = CollisionHandler()
particleHandler = ParticleHandler()

lPos = [0, 0]
prev_time = time.time()
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
    for particle in particleHandler.particles:
        particle.SetPos(particle.GetPos() + Vec2(diff))
    for wc in world: # Worldcolliders are tracked by rects only, so use numpy list subtraction
        wc.Move(diff)

    screen.blit(background_image, tuple(lPos))

    font = pygame.font.Font(None, 30)
    render_fps = font.render(str(int(clock.get_fps())), True, WHITE)
    screen.blit(render_fps, (0, 0))
    render_mousepos = font.render(str(pygame.mouse.get_pos()), True, WHITE)
    screen.blit(render_mousepos, (500, 0))

    colliders = world + objects # Everything the player can collide with

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
        base.x, base.y = (base.x * math.cos(rads)) - (base.y * math.sin(rads)),\
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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                GRAVITYON = False if GRAVITYON else True
        if event.type == pygame.KEYUP: # Cleaning up drive forces
            if event.key == pygame.K_SPACE:
                player.RemoveForce(player, "Drive")
            if event.key == pygame.K_LSHIFT:
                player.RemoveForce(player, "Drive")
            if event.key == pygame.K_j:
                ball.RemoveForce(ball, "Drive")
            if event.key == pygame.K_h:
                ball.RemoveForce(ball, "Drive")




    pygame.display.update()
    clock.tick(FPS)
