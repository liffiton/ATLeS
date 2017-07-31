import logging
import os

try:
    import pygame
    display_mocked = False
except ImportError:
    from fishbox.modulemock import MockClass
    pygame = MockClass("pygame")
    display_mocked = True


def _get_screen(xwin=False):
    """Initializes a new pygame screen using the framebuffer"""
    if display_mocked:
        xwin = True

    # Based on "Python GUI in Linux frame buffer"
    # http://www.karoltomala.com/blog/?p=679
    disp_no = os.getenv("DISPLAY")
    if disp_no:
        logging.info("Running under X display %s", disp_no)

    # Make sure that SDL_VIDEODRIVER is set
    if xwin:
        driver = 'x11'
    else:
        driver = 'directfb'   # alternatives: 'fbcon', 'svgalib'
    if not os.getenv('SDL_VIDEODRIVER'):
        os.putenv('SDL_VIDEODRIVER', driver)

    try:
        pygame.display.init()
    except pygame.error:
        logging.exception("Display init failed using driver: %s", driver)
        raise

    if xwin:
        size = (320, 200)
        options = 0
    else:
        # fullscreen
        info = pygame.display.Info()
        size = (info.current_w, info.current_h)
        logging.info("Framebuffer size: %d x %d", size[0], size[1])
        options = pygame.FULLSCREEN | pygame.DOUBLEBUF
    screen = pygame.display.set_mode(size, options)

    # Clear the screen to start
    screen.fill((0, 0, 0))
    pygame.mouse.set_visible(False)
    # Render the screen
    pygame.display.update()

    return screen


class Display(object):
    ''' Class for controlling the fishbox display '''

    def __init__(self):
        self._screen = _get_screen()

    def show_image(self, imgfile):
        logging.info("Loading background image: %s", imgfile)
        img = pygame.image.load(imgfile)
        imgscaled = pygame.transform.smoothscale(img, self._screen.get_size())
        self._screen.blit(imgscaled, (0, 0))
        pygame.display.flip()
