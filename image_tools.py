from queue import Queue
from threading import Thread
import pygame, logging


def resize_to_fill(base_img, size):
    return __resize(base_img, size, max)


def resize_to_fit(base_img, size):
    return __resize(base_img, size, min)


def __resize(base_img, size, strategy):
    base_size = base_img.get_size()
    scale_factor = strategy(float(size[0]) / base_size[0], float(size[1]) / base_size[1])
    img = pygame.transform.rotozoom(base_img, 0, scale_factor)
    final_size = img.get_size()
    position = ((size[0] - final_size[0]) / 2, (size[1] - final_size[1]) / 2)

    logging.getLogger('image_tools').debug("resize " + str(base_size) + " to fit " + str(size) + " (factor="
                                           + str(scale_factor) + ", final_size=" + str(final_size) + ", position="
                                           + str(position) + ")")

    return img, position


class Loader:
    def __init__(self, size=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.queue = Queue()
        self.size = size
        thread = Thread(target=self.__load)
        thread.setDaemon(True)
        thread.start()

    def __load(self):
        while True:
            filename, callback = self.queue.get()
            self.logger.debug("Worker.__load(filename=" + filename + ")")
            callback(self.__scale_down(pygame.image.load(filename).convert_alpha()))
            self.queue.task_done()

    def add_work(self, filename, callback):
        self.logger.debug("Worker.add_work(filename=" + filename + ")")
        self.queue.put((filename, callback))

    def join(self):
        self.queue.join()

    def __scale_down(self, base_img):
        if not self.size:
            return base_img
        base_size = base_img.get_size()
        scale_factor = max(self.size[0] / base_size[0], self.size[1] / base_size[1])
        if scale_factor < 1:
            self.logger.debug('scale down factor ' + str(scale_factor))
            return pygame.transform.rotozoom(base_img, 0, scale_factor)
        else:
            return base_img

