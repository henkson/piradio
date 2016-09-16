import pygame.constants as const
import pygame
import sys
import os
from scroll import ScrollPane, SelectionPane

__author__ = 'jeroen'


ScrSize = (320,240)
Origin = (0,0)

if __name__ == '__main__':

    pygame.init()
    screen = pygame.display.set_mode(ScrSize)
    clock = pygame.time.Clock()

    imgdesc = []
    for i in xrange(0,48):
        imgdesc.append(("PiTFTWeather/", str(i).zfill(2) + ".png"))
    imgdesc.append(("PiTFTWeather/", "na.png"))

    images = []
    print "start loading images..."
    for i in imgdesc:
        print "load: " + i[0]
        images.append(pygame.image.load(os.path.join(i[0],i[1])).convert())
    print "... loading images: done"

    #bg = pygame.Surface(ScrSize).convert()

    mybrowser = SelectionPane(images, ScrSize)
    worldSize = mybrowser.get_size()
    bg = pygame.Surface((worldSize[0], worldSize[1])).convert()

    pygame.display.set_caption("Example")
    initRect = pygame.Rect(screen.get_rect())
    initRect = pygame.Rect(0, 0, min(worldSize[0], ScrSize[0]), min(worldSize[1], ScrSize[1]))

    # sp = SwipePane(mybrowser, initRect, bg)
    sp = ScrollPane(mybrowser, initRect)
    sp.draw(bg)

    screen.blit(bg,Origin)
    pygame.display.flip()
    loop = True
    while loop:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type is pygame.QUIT:
                loop = False
            sp.update(event)
        changes = sp.draw(bg)
        screen.blit(bg,Origin)
        pygame.display.update(changes)
