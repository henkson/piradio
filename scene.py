__author__ = 'jeroen'


class Scene(object):
    manager = None

    def __init__(self):
        pass

    def draw(self, surface):
        raise NotImplementedError

    def clear(self, screen):
        raise NotImplementedError

    # def update(self):
    #     raise NotImplementedError

    def handle(self, event):
        raise NotImplementedError
