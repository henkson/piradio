from pygame.sprite import DirtySprite
import logging
from enum import Enum, unique


@unique
class Location(Enum):
    NORTH = ("North", (lambda sprite,screen: (sprite.rect.left,   -sprite.rect.height)))
    EAST  = ("East",  (lambda sprite,screen: (-sprite.rect.width, sprite.rect.top)))
    SOUTH = ("South", (lambda sprite,screen: (sprite.rect.left,   screen.height)))
    WEST  = ("West",  (lambda sprite,screen: (screen.width,       sprite.rect.top)))

    def __init__(self, name, strategy):
        self.strategy = strategy

    def calculate_disappear_location(self, sprite, screen):
        return self.strategy(sprite, screen)


class DisappearAppearSprite(DirtySprite):
    move_offset = 1

    def __init__(self,
                 location,  # Location enum, defines where the sprite must disappear to
                 position,  # x-y coordinates of self.rect.topleft
                 screen     # pygame.Rect object that indicates the entire screen
                 ):
        self.logger = logging.getLogger(self.__class__.__name__)
        DirtySprite.__init__(self)

        self.location = location
        self.base_position = position
        self.target_position = position
        self.screen = screen

        self.set_position(position)

    def update(self):
        diff_x = self.target_position[0] - self.rect.x
        if diff_x > 0:
            self.rect.x = min(self.rect.x + self.move_offset, self.target_position[0])
        elif diff_x < 0:
            self.rect.x = max(self.rect.x - self.move_offset, self.target_position[0])

        diff_y = self.target_position[1] - self.rect.y
        if diff_y > 0:
            self.rect.y = min(self.rect.y + self.move_offset, self.target_position[1])
        elif diff_y < 0:
            self.rect.y = max(self.rect.y - self.move_offset, self.target_position[1])

        if diff_x != 0 or diff_y != 0:
            self._make_dirty()

    def set_position(self, position, smooth=False):
        self.logger.debug(str(self) + '.set_position(' + str(position) + ')')
        self.base_position = position
        if smooth:
            self.target_position = position
        else:
            self.rect.topleft = position
        self._make_dirty()
        return self.rect.copy()

    def _make_dirty(self):
        if self.dirty < 2:
            self.dirty = 1

    def disappear(self):
        self.target_position = self.location.strategy(self, self.screen)

    def reappear(self):
        self.target_position = self.base_position