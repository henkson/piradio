from pitft.pitft import PiTFT
import pygame
import pygame.constants as const
import argparse
import logging

from scroll import ScrollPane
import player


class SceneManager:
    scene = None

    def __init__(self, screen, initial):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.screen = screen
        self.go_to(initial)

    def go_to(self, scene):
        self.logger.debug('go to ' + str(scene))
        self.scene = scene
        self.scene.manager = self
        self.scene.clear(self.screen)


class LoggerFactory:
    def __init__(self, base_get_logger, debugs, infos):
        self.base_get_logger = base_get_logger
        self.debugs = debugs
        self.infos = infos

    def getLogger(self, name):
        logger = self.base_get_logger(name)
        if self.debugs and name in self.debugs:
            logger.setLevel(logging.DEBUG)
        if self.infos and name in self.infos:
            logger.setLevel(logging.INFO)
        return logger


def main():
    # parse commandline args
    parser = argparse.ArgumentParser(description='MPD client for PiTFT.')
    parser.add_argument('-l', '--logfile', metavar='/path/to/logs/filename.log',
                        help='log messages to this file (default: log to console)')
    parser.add_argument('-s', '--stand-alone', action='store_true',
                        help='start as stand-alone (kiosk) application')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='enable verbose logging (default: verbose logging off)')
    parser.add_argument('-d', '--debug', metavar='LOGGER', action='append',
                        help='enable debug logging for specified loggers')
    parser.add_argument('-i', '--info', metavar='LOGGER', action='append',
                        help='set info logging for specified loggers')

    args = parser.parse_args()

    # initialize logging
    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    log_format = '%(levelname)-7s %(asctime)-15s %(name)s: %(message)s'
    logging.basicConfig(format=log_format,level=log_level)

    logger_factory = LoggerFactory(logging.getLogger, args.debug, args.info)
    logging.getLogger = logger_factory.getLogger

    logger = logging.getLogger('main')
    logger.info("==== here we go again")
    logger.debug("commandline args: %s", str(args))

    mytft = PiTFT(args.stand_alone)
    init_rect = pygame.Rect(mytft.screen.get_rect())
    bg = pygame.Surface(mytft.screen.get_size()).convert()

    mympd = mytft.mympd  # PiMPD()
    playlists = mympd.init_playlists()

    # SCENE 1 -- Playlist selector
    playlist_selector = ScrollPane(playlists, init_rect)

    # SCENE 2 -- Player
    myplayer = player.Player(mytft, playlist_selector)
    playlist_selector.player = myplayer

    # scene manager
    manager = SceneManager(mytft.screen, playlist_selector)

    manager.scene.draw(bg)
    origin = (0,0)
    mytft.screen.blit(bg, origin)

    pygame.display.flip()
    loop = True
    while loop:
        try:
            mytft.clock_tick()
            for event in pygame.event.get():
                if event.type == const.K_ESCAPE or event.type is pygame.QUIT:
                    loop = False
                    break
                manager.scene.handle(event)
            changes = manager.scene.draw(mytft.screen)
            pygame.display.update(changes)
        except Exception as e:
            logger.exception("Error occured: %s", e)

    mytft.exit()


if __name__ == '__main__':
    main()
