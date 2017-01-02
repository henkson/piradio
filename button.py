import logging
import os
import pygame
from sprite import DisappearAppearSprite as MySprite

__author__ = 'jeroen'


class Button(MySprite):

    def __init__(self, name, callback, location, position=(0,0), screen=pygame.Rect(0,0,320,240)):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = name

        self.image, self.rect = self.load_image(name)

        self.callback = callback
        MySprite.__init__(self, location, position, screen)

    def load_image(self, name):
        filepath = 'player_icons'
        filename = name + '.png'
        try:
            image = pygame.image.load(os.path.join(filepath, filename)).convert_alpha()
        except pygame.error:
            self.logger.warn('button image ' + filename + ' not found, using fallback instead')
            image = pygame.image.load(os.path.join(filepath, 'error.png')).convert_alpha()
        return image, image.get_rect()

    def set_visible(self, visible):  # visible is boolean
        vis = 1 if visible else 0
        change = self.visible != vis
        if change:
            self.logger.debug(self.name + '.set_visible(' + str(visible) + ')')
            self.visible = vis
            self._make_dirty()
        return change

    def execute(self):
        if self.visible:
            self.callback()
        else:
            self.logger.debug(self.name + ' not executed because I\'m not visible!')

    def __str__(self):
        return self.name


class ToggleButton(Button):

    def __init__(self, name1, callback1, name2, callback2, location):
        super(ToggleButton, self).__init__(name1, callback1, location)
        self.name = name1 + '/' + name2
        image2, _ = self.load_image(name2)

        self.actions = {name1:[self.image, self.callback],
                        name2:[image2, callback2]}

        self.current = name1

    def execute(self):
        if self.visible:
            self.actions[self.current][1]()
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
