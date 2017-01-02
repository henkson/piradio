import math
import pygame
import colors
import logging
import threading
from scene import Scene
from image_tools import resize_to_fit
from button import Button

__author__ = 'jeroen'


origin = (0, 0)
button_size = 50
transparent = colors.black
filled = colors.red.correct_gamma(100)


class ScrollPane(Scene):
    player = None

    playlistButtons = []
    allSprites = pygame.sprite.LayeredDirty()

    def __init__(self,
                 playlists,
                 init_rect):
        super(ScrollPane, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.background = pygame.Surface(init_rect.size).convert()
        self.background.fill(colors.grey)
        self.view_port = init_rect

        self.thumb_size = calc_img_size(init_rect.size[0])
        x, y = 0, 0
        for playlist in playlists:
            x, y = self.create_thumb(playlist, x, y)

        self.scrolling = False
        self.offset = [0, 0]
        self.desired_offset = [0, 0]

        self.up = self.create_button('up', (lambda: self.scroll('up')), 320-30-10, 5)
        self.down = self.create_button('down', (lambda: self.scroll('down')), 320-30-10, 240-30-10)
        self.topleft = self.create_button('topleft', self.go_to_player, 5, 5)

    def create_thumb(self, playlist, x, y):
        base_pos = (border + x * (self.thumb_size[0] + spacing), border + y * (self.thumb_size[1] + spacing))
        new_button = PlaylistButton(playlist, self.thumb_size, base_pos, self)
        self.playlistButtons.append(new_button)
        self.allSprites.add(new_button)

        if x == (nb_cols - 1):
            y += 1
        x = (x + 1) % nb_cols

        return x,y

    def create_button(self, name, callback, x, y):
        btn = Button(name, callback, None, (x,y))
        self.allSprites.add(btn)
        return btn

    def clear(self, screen):
        screen.blit(self.background, (0,0))
        pygame.display.flip()
        for f in self.allSprites:
            f.dirty = 1
        self.allSprites.clear(screen, self.background)

    def go_to_player(self):
        self.manager.go_to(self.player)

    def start_playlist(self, playlist):
        self.manager.go_to(self.player.start_playlist(playlist))

    def handle(self, event):
        # if __debug__:
        #     print "Player: handle(" + str(event) + ")"
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_buttons = [b for b in self.allSprites if b.rect.collidepoint(event.pos)]
            if clicked_buttons:
                button = clicked_buttons[-1] # if multiple buttons on top of each other: topmost button only
                self.logger.debug("clicked on " + str(button) + " button")
                button.execute()

    def scroll(self, updown):
        """
        :param updown: 'up' or 'down'
        :return:
        """
        if self.playlistButtons[1].move != 0:
            # we are already scrolling, ignore any other request
            self.logger.debug("-- already scrolling, ignore")
            return

        switcher = { 'up': +1,  'down': -1 }
        offset = switcher.get(updown) * 2 * (self.thumb_size[1] + spacing)
        self.logger.debug("scroll offset " + str(offset))
        for pb in self.playlistButtons:
            pb.do_move(offset)

    def draw(self, surface):
        """
        :param surface: the surface to blit on
        :return: list of updates
        """
        self.up.set_visible(self.playlistButtons[1].rect.topleft[1] <= 0)
        self.down.set_visible(self.playlistButtons[-1].rect.bottomleft[1] >= self.background.get_size()[1])

        self.allSprites.update()
        return self.allSprites.draw(surface)


nb_cols = 3
border = 13
spacing = 12
scroll_width = 0


def calc_img_size(screen_width):
    """ return image-size
    :param screen_width: width of the screen to display this browser
    :return: tuple (width, height)
    """
    img_width = (screen_width - scroll_width - 2 * border - (nb_cols - 1) * spacing) / nb_cols
    #           [------------] [------------] [----------] [------------------------] [-------]
    #                  |             |              |                |                    `------> aantal icoontjes in de breedte
    #                  |             |              |                `---------------------------> ruimte tussen icoontjes
    #                  |             |              `--------------------------------------------> rand links en rechts
    #                  |             `-----------------------------------------------------------> pixels voor scrollbar rechts
    #                  `-------------------------------------------------------------------------> breedte van touchscreen
    return img_width, img_width


class PlaylistButton(pygame.sprite.DirtySprite):
    def __init__(self, playlist, thumb_size, base_pos, scroll_pane):
        pygame.sprite.DirtySprite.__init__(self)

        self.lock = threading.Lock()
        self.lock.acquire()

        try:
            self.playlist = playlist
            self.thumb_size = thumb_size

            self.playlist.add_listener(self)

            self.image, relpos = resize_to_fit(playlist.cover_img, thumb_size)
            self.scroll_pane = scroll_pane
            self.rect = self.image.get_rect()
            self.rect.topleft = base_pos[0] + relpos[0], base_pos[1] + relpos[1]

            self.move = 0
        finally:
            self.lock.release()

    def playlist_updated(self):
        self.lock.acquire()
        try:
            old_size = self.image.get_size()
            old_topleft = self.rect.topleft
            self.image, _ = resize_to_fit(self.playlist.cover_img, self.thumb_size)

            final_size = self.image.get_size()
            self.rect = self.image.get_rect()
            self.rect.topleft = old_topleft[0] + (old_size[0] - final_size[0]) / 2,\
                                old_topleft[1] + (old_size[1] - final_size[1]) / 2

            self.dirty = 1
        finally:
            self.lock.release()

    def update(self):
        if self.move > 0:
            offset = min(self.move, 10)
        elif self.move < 0:
            offset = max(self.move,-10)
        else:
            offset = 0
        if offset != 0:
            self.rect = self.rect.move((0, offset))
            self.move -= offset
            self.dirty = 1

    def do_move(self, offset):
        self.move = offset

    def execute(self):
        self.scroll_pane.start_playlist(self.playlist)

    def __str__(self):
        return 'PlaylistButton ' + str(self.playlist)
