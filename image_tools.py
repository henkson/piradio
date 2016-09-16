import pygame, logging


def resize_to_fill(base_img, size):
    base_size = base_img.get_size()
    scale_factor = max(float(size[0]) / base_size[0], float(size[1]) / base_size[1])
    img = pygame.transform.rotozoom(base_img, 0, scale_factor)
    final_size = img.get_size()
    position = ((size[0] - final_size[0]) / 2, (size[1] - final_size[1]) / 2)

    logging.getLogger('image_tools').debug("resize " + str(base_size) + " to fit " + str(size) + " (factor="
                                           + str(scale_factor) + ", final_size=" + str(final_size) + ", position="
                                           + str(position) + ")")

    return img, position


def resize_to_fit(base_img, size):
    base_size = base_img.get_size()
    scale_factor = min(float(size[0]) / base_size[0], float(size[1]) / base_size[1])
    img = pygame.transform.rotozoom(base_img, 0, scale_factor)
    final_size = img.get_size()
    position = ((size[0] - final_size[0]) / 2, (size[1] - final_size[1]) / 2)

    logging.getLogger('image_tools').debug("resize " + str(base_size) + " to fit " + str(size) + " (factor="
                                           + str(scale_factor) + ", final_size=" + str(final_size) + ", position="
                                           + str(position) + ")")

    return img, position
