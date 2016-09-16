import logging
import os
import pygame

__author__ = 'jeroen'


class Button(pygame.sprite.DirtySprite):
    # btn_size = (30,30)

    def __init__(self, name, callback):
        self.logger = logging.getLogger(self.__class__.__name__)
        pygame.sprite.DirtySprite.__init__(self)
        self.name = name

        self.image = self.load_image(name)
        self.rect = self.image.get_rect()

        self.callback = callback

    def load_image(self, name):
        filepath = 'player_icons'
        filename = name + '.png'
        try:
            image = pygame.image.load(os.path.join(filepath, filename)).convert_alpha()
        except pygame.error:
            self.logger.warn('button image ' + filename + ' not found, using fallback instead')
            image = pygame.image.load(os.path.join(filepath, 'error.png')).convert_alpha()
        return image

    def set_position(self, x, y):
        self.logger.debug(self.name + '.set_position(' + str((x,y)) + ')')
        self.rect.x, self.rect.y = x, y
        self._make_dirty()
        return self.rect.copy()

    def set_visible(self, visible):  # visible is boolean
        vis = 1 if visible else 0
        change = self.visible != vis
        if change:
            self.logger.debug(self.name + '.set_visible(' + str(visible) + ')')
            self.visible = vis
            self._make_dirty()
        return change

    def _make_dirty(self):
        if self.dirty != 2:
            self.dirty = 1

    def execute(self):
        if self.visible:
            self.callback()
        else:
            self.logger.debug(self.name + ' not executed because I\'m not visible!')


class ToggleButton(Button):

    def __init__(self, name1, callback1, name2, callback2):
        super(ToggleButton, self).__init__(name1, callback1)
        self.name = name1 + '/' + name2
        image2 = self.load_image(name2)

        self.actions = {name1:[self.image, self.callback],
                        name2:[image2, callback2]}

        # self.images = [self.image, image2]
        # self.callbacks = [self.callback, callback2]
        self.current = name1

    def execute(self):
        if self.visible:
            self.actions[self.current][1]()
            # self.callbacks[self.current]()
            # self.set_status((self.current + 1) % len(self.images))
        else:
            self.logger.debug(self.name + ' not executed because I\'m not visible!')

    def set_action(self, action):
        if self.current != action:
            self.logger.debug(self.name + ' set action: ' + action)

            self.current = action
            self.image = self.actions[self.current][0]
            self._make_dirty()
        else:
            self.logger.debug(self.name + ' action not updated: was already ' + action)
