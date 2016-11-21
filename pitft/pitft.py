import os
import sys
import platform
import pygame
import colors
import logging
import mympd


def init_desktop():
    pygame.display.init()
    pygame.display.set_caption("Example")
    screen_size = (320,240)
    screen = pygame.display.set_mode(screen_size)

    return screen


def init_pitft():
    """Ininitializes a new pygame screen using the framebuffer"""
    # Based on "Python GUI in Linux frame buffer"
    # http://www.karoltomala.com/blog/?p=679

    disp_no = os.getenv("DISPLAY")
    if disp_no:
        print("I'm running under X display = {0}".format(disp_no))

    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')

    # Select frame buffer driver
    # Make sure that SDL_VIDEODRIVER is set
    driver = 'fbcon'
    if not os.getenv('SDL_VIDEODRIVER'):
        os.putenv('SDL_VIDEODRIVER', driver)
    try:
        pygame.display.init()
    except pygame.error:
        print('Driver: {0} failed.'.format(driver))
        exit(0)

    size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    screen = pygame.display.set_mode(size, pygame.FULLSCREEN)

    pygame.mouse.set_visible(False)

    return screen


class PiTFT:
    platform = platform.system()

    def __init__(self, stand_alone):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stand_alone = stand_alone

        if self.platform == "Linux":
            self.screen = init_pitft()
            self.mympd = mympd.PiMPD()
        elif self.platform == "Windows":
            self.screen = init_desktop()
            self.mympd = mympd.WinMPD()
        else:
            raise Exception("unknown platform: " + self.platform)

        # Clear the screen to start
        self.screen.fill(colors.yellow)

        # "Splash" image
        base_img = pygame.image.load(os.path.join('player_icons', 'unknown.png')).convert_alpha()
        img = pygame.transform.scale(base_img, (240,240))
        self.screen.blit(img, (40,0))

        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()

        pygame.init()

        self.clock = pygame.time.Clock()

    def clock_tick(self):
        if self.platform == "Linux":
            self.clock.tick(360)
        elif self.platform == "Windows":
            self.clock.tick(180)

    def exit(self):
        self.logger.info("exit")

        self.screen.fill(colors.black)
        pygame.display.update()

        if self.stand_alone and self.platform == "Linux":
            self.logger.info("system halt")
            os.system("sudo halt")
        sys.exit(0)

    def __del__(self):
        """Destructor to make sure pygame shuts down, etc."""
