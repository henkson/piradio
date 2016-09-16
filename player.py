import os
import logging

import pygame

from button import Button, ToggleButton
import colors
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
        self.alpha = -25.5

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
            # alpha = self.image.get_alpha() + self.alpha
            # if alpha >= 255 or alpha <= 0:
            #     self.alpha = -self.alpha
            # value = min(max(int(alpha), 0), 255)
            # self.logger.debug("image.set_alpha(" + str(value) + ")")
            # self.image.set_alpha(value)
            import time
            t = int(time.time() * 1.5) % 2 == 0
            vis = 1 if t else 0
            if self.visible != vis:
                self.logger.debug("self.set_visible(" + str(vis) + ")")
                self.visible = vis
                self._make_dirty()
            else:
                #self.logger.debug("self.visible = " + str(self.visible))
                pass

    def _make_dirty(self):
        if self.dirty != 2:
            self.dirty = 1

    def swap_image(self):
        # randomly choose another image
        # todo: kan dit zelf geimplementeerd worden als een "LayeredDirty", met X sprites waarvan er telkens maar 1 zichtbaar is??
        pass


class Player(Scene):

    playlist = None
    cover_img = None
    dirty = True

    sprites = pygame.sprite.LayeredDirty()
    # sprites = pygame.sprite.Group()

    def __init__(self,
                 mytft,  # PiTFT
                 browser):    # ScrollPane
        super(Player, self).__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mytft = mytft
        self.mympd = mytft.mympd

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

        # positioning the buttons on the screen
        # i = 0
        # screen = pygame.display.get_surface()
        # self.screen_size = screen.get_rect()
        self.screen_size = browser.view_port.size

        self.background = pygame.display.get_surface()
        self.background.convert()

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

        self.font = pygame.font.Font(None, 24)

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
            for button in clicked_buttons:
                self.logger.debug("clicked on " + str(button.name) + " button")
                button.execute()

    def draw(self, surface):
        result = []

        status = self.mympd.status()

        # proceed button
        try:
            # result.append(self.proceed.rect.copy())
            progress = float(status['elapsed']) / int(self.mympd.currentsong()['time'])
        except KeyError:  # can't find key 'elapsed' or 'time'
            progress = 0

        change = self.progress.set_progress(progress) \
                 or self.previous_btn.set_visible('song' in status and status['song'] > 0) \
                 or self.next_btn.set_visible('nextsong' in status)
        if change:
            self.dirty = True  # fixme: dit zou toch niet moeten als we LayeredDirty gebruiken?? :-(
            pass

        screen_size = surface.get_size()

        # album-art tekenen
        if self.dirty:
            self.background.blit(self.cover_img[0], self.cover_img[1])
            result.append(surface.blit(self.background, (0,0)))
            for s in self.sprites:
                s._make_dirty()
            self.sprites.clear(surface, self.background)

        # sprites tekenen
        self.sprites.update()
        result.extend(self.sprites.draw(surface))
        self.dirty = False

        # altijd: huidig nummer, huidige positie
        label1 = self.font.render(str(status['track']), 1, colors.blue)
        label2 = self.font.render(status['title'], 1, colors.red)
        result.append(surface.blit(label1, (20, 60)))
        result.append(surface.blit(label2, (20, 100)))

        return result

    def x_offset(self, i, nb):
        return (30 * i) + ((float(self.screen_size[0]) - (nb * 30)) / (nb + 1)) * (i + 1)


if __name__ == '__main__':
    # test code to immediately run player
    import pitft

    pygame.display.init()
    pygame.display.set_caption("Example")
    screen_size = (320,240)
    screen = pygame.display.set_mode(screen_size)

    clock = pygame.time.Clock()

    mytft = pitft.PiTFT(False)
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
            self.cover_img = pygame.image.load(os.path.join('player_icons', 'unknown.png')).convert_alpha()

    playlist = MyPlaylist()

    screen.fill(colors.yellow)
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
        changes = myplayer.draw(bg)
        # screen.blit(bg, (0,0))
        pygame.display.update(changes)

    mytft.exit()


