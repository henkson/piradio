import math
import pygame
import colors
import logging
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

    buttons = pygame.sprite.LayeredDirty()

    def __init__(self,
                 playlists,
                 init_rect):
        super(ScrollPane, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.browser = SelectionPane(playlists, init_rect.size)
        self.world_size = self.browser.get_size()
        self.view_port = init_rect

        self.scrolling = False
        self.dirty = True
        self.offset = [0, 0]
        self.desired_offset = [0, 0]

        self.scroll_rect = pygame.Rect(0, 0, 0, 240)

        self.up = self.create_button('up', (lambda: self.scroll('up')), 320-30-10, 5)
        self.down = self.create_button('down', (lambda: self.scroll('down')), 320-30-10, 240-30-10)
        self.topleft = self.create_button('topleft', self.go_to_player, 5, 5)

    def create_button(self, name, callback, x, y):
        btn = Button(name, callback)
        btn.set_position(x,y)
        btn.dirty = 2  # we force dirty state to make sure button is drawn on top of blitted scrollpane
        self.buttons.add(btn)
        return btn

    def go_to_player(self):
        self.manager.go_to(self.player)
        self.dirty = True

    def handle(self, event):
        # if __debug__:
        #     print "Player: handle(" + str(event) + ")"
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_buttons = [b for b in self.buttons if b.rect.collidepoint(event.pos)]
            for button in clicked_buttons:
                self.logger.debug("clicked on " + str(button.name) + " button")
                button.execute()
            if clicked_buttons.__len__() == 0:
                selected = self.browser.update(event, self.offset)
                if selected is not None:
                    self.dirty = True
                    self.manager.go_to(self.player.start_playlist(selected))

    def scroll(self, updown):
        """
        :param updown: 'up' or 'down'
        :return:
        """
        if self.desired_offset[1] != self.offset[1]:
            # we are already scrolling, ignore any other request
            self.logger.debug("-- already scrolling, ignore")
            return

        switcher = { 'up': -1,  'down': +1 }
        for i, p in enumerate(self.browser.get_scroll_positions()):
            if p == self.offset[1]:
                break
        i += switcher.get(updown)
        if 0 <= i < len(self.browser.get_scroll_positions()):
            self.desired_offset[1] = self.browser.get_scroll_positions()[i]
            self.logger.debug("scroll: " + str(self.offset[1]) + " -> " + str(self.desired_offset[1]))
            self.dirty = True

    def draw(self, surface):
        """
        :param surface: the surface to blit on
        :return: list of updates
        """
        result = []
        step = 3  # 10  # nb of pixels to move at once
        if self.dirty:
            if self.desired_offset[1] > self.offset[1]:
                self.offset[1] += step
                self.offset[1] = min(self.offset[1], self.desired_offset[1])
            elif self.desired_offset[1] < self.offset[1]:
                self.offset[1] -= step
                self.offset[1] = max(self.offset[1], self.desired_offset[1])

            self.up.set_visible(self.offset[1] > 0)
            self.down.set_visible(self.offset[1] + self.view_port.size[1] < self.world_size[1])

            result.append(surface.blit(self.browser.get_view(), self.view_port.topleft, (self.offset, self.view_port.size)))

            self.buttons.update()
            drawn = self.buttons.draw(surface)

            if drawn: #fixme: als we LayeredDirty gebruiken zal dit altijd True zijn
                result.extend(drawn)

            # for b in self.buttons.sprites():
            #     if b.visible == 1:
            #         b.draw(surface)

            self.dirty = self.desired_offset[1] != self.offset[1]

        return result


nb_cols = 3
border = 13
spacing = 12
scroll_width = 0


class SelectionPane:

    def __init__(self,
                 playlists,  # list of Playlist objects
                 scr_size    # in pixels
                 ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.playlists = playlists
        self.img_size = self.calc_img_size(scr_size[0])
        nb_rows = int(math.ceil(float(len(playlists)) / nb_cols))
        view_size = self.calc_size((nb_cols, nb_rows))
        self.view = pygame.Surface(view_size)

        # grey background
        self.view.fill(colors.grey)

        # paint all images on surface
        x, y = 0, 0
        row_starts = []
        for i, playlist in enumerate(playlists):
            img, relpos = resize_to_fit(playlist.cover_img, self.img_size)
            # img = pygame.transform.scale(playlist.cover_img.convert(), self.img_size)
            base_pos = (border + x * (self.img_size[0] + spacing), border + y * (self.img_size[1] + spacing))
            pos = (base_pos[0] + relpos[0], base_pos[1] + relpos[1])
            self.view.blit(img, pos)
            if i == 0 or row_starts[-1] != base_pos[1]:
                row_starts.append(base_pos[1])

            if x == (nb_cols - 1):
                y += 1
            x = (x + 1) % nb_cols

        # calculate utilities: positions at which scrolling needs to stop
        visible_rows = 0
        while ((visible_rows + 1) * (self.img_size[1] + spacing)) < scr_size[1]:
            visible_rows += 1
        overschot = (scr_size[1] - (visible_rows * self.img_size[1] + (visible_rows - 1) * spacing)) / 2
        tmp_scroll_positions = [0]
        while tmp_scroll_positions[-1] + scr_size[1] < view_size[1]:
            next_pos = row_starts[visible_rows * len(tmp_scroll_positions)] - overschot
            next_pos = min(next_pos, view_size[1] - scr_size[1])
            tmp_scroll_positions.append(next_pos)
        # readonly-copy of scroll_positions
        self.scroll_positions = tuple(tmp_scroll_positions)

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("Browser created for screen size %s with:", str(scr_size))
            self.logger.debug(" img_size %s", str(self.img_size))
            self.logger.debug(" %d visible rows", visible_rows)
            self.logger.debug(" view size is %s", str(view_size))
            self.logger.debug(" rows start at %s", str(row_starts))
            self.logger.debug(" scroll positions are %s", str(self.scroll_positions))

    def calc_img_size(self, screen_width):
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

    def calc_size(self, nb_cols_rows):
        xsize = border + nb_cols_rows[0] * (self.img_size[0] + spacing) + (border - spacing)
        ysize = border + nb_cols_rows[1] * (self.img_size[1] + spacing) + (border - spacing)
        return xsize, ysize

    def update(self, event, offset):  # pygame event, must not be None
        if event.type == pygame.USEREVENT or event.type == pygame.MOUSEBUTTONDOWN:
            x = event.pos[0] + offset[0]
            y = event.pos[1] + offset[1]
            col = int(math.floor((x - border) / (self.img_size[0] + spacing)))
            row = int(math.floor((y - border) / (self.img_size[1] + spacing)))
            nb = (row * nb_cols) + col
            playlist = self.playlists[nb]
            self.logger.debug("%s -> %s -> %s -> %s -> %s", str(event.pos), str((x,y)), str((col,row)), str(nb), playlist.playlist)
            return playlist

    def get_scroll_positions(self):
        return self.scroll_positions

    def get_size(self):
        return self.view.get_size()

    def get_view(self):
        return self.view
