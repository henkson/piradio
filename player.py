import os
import logging

import pygame

from button import Button, ToggleButton
import colors
from pitft.pitft import PiTFT
from scene import Scene
from image_tools import resize_to_fill


class Progress(pygame.sprite.DirtySprite):

    y = 150

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        pygame.sprite.DirtySprite.__init__(self)

        filepath = 'player_icons'
        filename = 'proceed_02.png'
        try:
            self.image = pygame.image.load(os.path.join(filepath, filename)).convert_alpha()
        except pygame.error:
            self.logger.warn('progress image ' + filename + ' not found, using fallback instead')
            self.image = pygame.image.load(os.path.join(filepath, 'proceed.png')).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.top = self.y

        screen = pygame.display.get_surface()
        self.area = screen.get_rect()

        self.blinking = False

    def set_progress(self,
                     progress):  # value between 0 and 1
        x = int((self.area.right - self.rect.width) * progress)
        if x == 0:
            self.swap_image()
        change = self.rect.left != x
        if change:
            self.rect.left = x
            self._make_dirty()
        return change

    def set_blinking(self, blinking):
        if self.blinking != blinking:
            self.logger.debug("set_blinking(" + str(blinking) + ")")
            if not blinking:
                # self.image.set_alpha(255)
                # self.alpha = -abs(self.alpha)
                self.visible = 1
            self.blinking = blinking
            self._make_dirty()

    def update(self):
        if self.blinking:
            import time
            t = int(time.time() * 1.5) % 2 == 0
            vis = 1 if t else 0
            if self.visible != vis:
                self.logger.debug("self.set_visible(" + str(vis) + ")")
                self.visible = vis
                self._make_dirty()

    def _make_dirty(self):
        if self.dirty != 2:
            self.dirty = 1

    def swap_image(self):
        # randomly choose another image
        # todo: kan dit zelf geimplementeerd worden als een "LayeredDirty", met X sprites waarvan er telkens maar 1 zichtbaar is??
        pass


class Gradient(pygame.sprite.DirtySprite):
    def __init__(self, size, position, top_down=True, fill=1.0):
        self.logger = logging.getLogger(self.__class__.__name__)
        pygame.sprite.DirtySprite.__init__(self)

        surface = pygame.Surface(size).convert_alpha()
        surface.fill(pygame.Color(0,0,0,0)) # fully transparent

        assert 0 <= fill <= 1

        gradient = pygame.image.load(os.path.join('player_icons', 'gradient-black-transp.png')).convert_alpha()
        gradient = pygame.transform.scale(gradient, (size[0], int(size[1] * fill)))

        surface.fill(colors.black, pygame.Rect(0, 0, size[0], size[1] * (1 - fill)))
        surface.blit(gradient, (0,size[1] - size[1]*fill))

        if top_down:
            self.image = surface
        else:
            self.image = pygame.transform.flip(surface, False, True)
        self.rect = self.image.get_rect()
        self.set_position(*position)
        self.logger.debug(str(self) + ': init done, image=' + str(self.image) + ", rect=" + str(self.rect))

    def set_position(self, x, y):
        self.logger.debug(str(self) + '.set_position(' + str((x,y)) + ')')
        self.rect.x, self.rect.y = x, y
        self._make_dirty()
        return self.rect.copy()

    def _make_dirty(self):
        if self.dirty != 2:
            self.dirty = 1


class InfoText(pygame.sprite.DirtySprite):
    def __init__(self, width, position):
        self.logger = logging.getLogger(self.__class__.__name__)
        pygame.sprite.DirtySprite.__init__(self)

        self.font = pygame.font.Font(None, 24)

        self.rect = pygame.Rect(position,(width,20))

        self.text = ""
        self.image = self._create_surface()

        self.logger.debug(str(self) + ': init done, image=' + str(self.image) + ", rect=" + str(self.rect))

    def set_text(self, text):
        if self.text != text:
            self.logger.debug(str(self) + '.set_text(' + text + ')')
            self.text = text
            self.image = self._create_surface()

    def _create_surface(self):
        surface = pygame.Surface((self.rect.width, self.rect.height)).convert_alpha()
        surface.fill(pygame.Color(0,0,0,0)) # fully transparent
        surface.blit(self.font.render(self.text, 1, colors.grey), (5, 0))
        self._make_dirty()
        return surface

    def set_position(self, x, y):
        self.logger.debug(str(self) + '.set_position(' + str((x,y)) + ')')
        self.rect.x, self.rect.y = x, y
        self._make_dirty()
        return self.rect.copy()

    def _make_dirty(self):
        if self.dirty != 2:
            self.dirty = 1


class Player(Scene):

    playlist = None
    cover_img = None
    dirty = True

    sprites = pygame.sprite.LayeredDirty()

    def __init__(self,
                 mytft,  # PiTFT
                 browser):    # ScrollPane
        super(Player, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mytft = mytft
        self.mympd = mytft.mympd

        self.screen_size = browser.view_port.size

        self.top_grad = Gradient(size=(self.screen_size[0],45),position=(0,0))
        self.sprites.add(self.top_grad)
        self.bottom_grad = Gradient(size=(self.screen_size[0],60),position=(0,self.screen_size[1]-60), top_down=False, fill=0.5)
        self.sprites.add(self.bottom_grad)

        self.previous_btn = self.create_button('previous', self.mympd.previous)
        self.next_btn = self.create_button('next', self.mympd.next)
        self.play_btn = self.create_toggle_button('play', self.play, 'pause', self.pause)
        self.stop_btn = self.create_button('stop', self.stop)
        self.list_btn = self.create_button('list', (lambda: self.go_to(browser)))
        self.exit_btn = self.create_button('exit', self.exit)
        self.vol_down_btn = self.create_button('vol_down', (lambda: self.set_vol(int(self.mympd.status()['volume']) - 5)))
        self.vol_up_btn = self.create_button('vol_up', (lambda: self.set_vol(int(self.mympd.status()['volume']) + 5)))

        # self.proceed = self.create_button('proceed', (lambda: 1))
        self.progress = Progress()
        self.sprites.add(self.progress)

        self.info_text = InfoText(self.screen_size[0], (0,self.screen_size[1]-20))
        self.sprites.add(self.info_text)

        self.background = pygame.display.get_surface().convert()

        # buttons at bottom of screen, from left to right
        y = self.screen_size[1] - 45 - self.x_offset(0, 7)

        btns = [self.previous_btn, self.next_btn, self.play_btn, self.stop_btn, self.vol_down_btn, self.vol_up_btn]
        for i in range(len(btns)):
            x = self.x_offset(i, len(btns))
            btns[i].set_position(x,y)

        # buttons at top right corner of the screen, from right to left
        y = self.x_offset(0,7)
        self.exit_btn.set_position(self.x_offset(len(btns)-1, len(btns)),y)

        i -= 1
        x = self.x_offset(i, len(btns))
        self.list_btn.set_position(x,y)

    def create_button(self, name, callback):
        btn = Button(name, callback)
        self.sprites.add(btn)
        return btn

    def create_toggle_button(self, name1, callback1, name2, callback2):
        btn = ToggleButton(name1, callback1, name2, callback2)
        self.sprites.add(btn)
        return btn

    def stop(self):
        self.mympd.stop()
        self.play_btn.set_action('play')
        self.progress.set_blinking(False)

    def start_playlist(self, playlist):
        self.logger.info("start playing " + str(playlist))
        self.playlist = playlist
        self.cover_img = resize_to_fill(playlist.cover_img, self.screen_size)

        self.dirty = True

        self.stop()
        self.mympd.clear()
        self.mympd.load(self.playlist.playlist)
        self.play()

        return self

    def play(self):
        self.mympd.play()
        self.play_btn.set_action('pause')
        self.progress.set_blinking(False)

    def pause(self):
        self.mympd.pause()
        self.play_btn.set_action('play')
        self.progress.set_blinking(True)

    def set_vol(self, vol):
        minmax = (0,100)
        real_vol = min(max(vol, minmax[0]), minmax[1])

        self.mympd.setvol(real_vol)

        self.vol_down_btn.set_visible(real_vol != minmax[0])
        self.vol_up_btn.set_visible(real_vol != minmax[1])

    def go_to(self, scene):
        self.dirty = True
        self.manager.go_to(scene)

    def exit(self):
        self.stop()
        self.mytft.exit()

    def handle(self, event):
        # if __debug__:
        #     print "Player: handle(" + str(event) + ")"
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_buttons = [b for b in self.sprites if b.rect.collidepoint(event.pos)]
            if clicked_buttons:
                button = clicked_buttons[-1] # if multiple buttons on top of each other: topmost button only
                self.logger.debug("clicked on " + str(button.name) + " button")
                button.execute()

    def clear(self, screen):
        self.sprites.clear(screen, self.cover_img[0])

    def draw(self, surface):
        result = []

        status = self.mympd.status()

        # proceed button
        try:
            progress = float(status['elapsed']) / int(self.mympd.currentsong()['time'])
        except KeyError:  # can't find key 'elapsed' or 'time'
            progress = 0

        self.progress.set_progress(progress)
        self.previous_btn.set_visible('song' in status and int(status['song']) > 0)
        self.next_btn.set_visible('nextsong' in status)
        if 'title' in status:
            text = status['title']
        else:
            text = "(?)"
        if 'track' in status:
            text = str(status['track']) + " - " + text
        elif 'song' in status:
            text = str(int(status['song']) + 1) + " - " + text
        self.info_text.set_text(text)

        # album-art tekenen
        if self.dirty:
            self.background.blit(self.cover_img[0], self.cover_img[1])
            surface.blit(self.background, (0,0))
            pygame.display.flip()
            for s in self.sprites:
                s._make_dirty()
            self.sprites.clear(surface, self.background)

        # sprites tekenen
        self.sprites.update()
        result.extend(self.sprites.draw(surface))
        self.dirty = False

        return result

    def x_offset(self, i, nb):
        return (30 * i) + ((float(self.screen_size[0]) - (nb * 30)) / (nb + 1)) * (i + 1)


if __name__ == '__main__':
    # test code to immediately run player
    log_level = logging.DEBUG
    log_format = '%(levelname)-7s %(asctime)-15s %(name)s: %(message)s'
    logging.basicConfig(format=log_format,level=log_level)

    pygame.display.init()
    pygame.display.set_caption("Example")

    clock = pygame.time.Clock()

    mytft = PiTFT(False)
    screen = mytft.screen
    init_rect = pygame.Rect(screen.get_rect())
    bg = pygame.Surface(screen.get_size()).convert()

    class MyBrowser:
        def __init__(self):
            self.view_port = init_rect
    browser = MyBrowser()

    myplayer = Player(mytft, browser)

    class MyPlaylist:
        def __init__(self):
            self.playlist = "test"
            self.cover_img = pygame.image.load(os.path.join('player_icons', 'Cover.png')).convert_alpha()
    playlist = MyPlaylist()

    pygame.display.flip()
    myplayer.start_playlist(playlist)
    loop = True
    while loop:
        clock.tick(180)
        for event in pygame.event.get():
            if event.type == pygame.constants.K_ESCAPE or event.type is pygame.QUIT:
                loop = False
                break
            myplayer.handle(event)
        pygame.display.update(myplayer.draw(screen))

    mytft.exit()


