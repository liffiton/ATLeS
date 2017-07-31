import os
import pygame
import time


def get_screen(xwin=False):
    """Initializes a new pygame screen using the framebuffer"""
    # Based on "Python GUI in Linux frame buffer"
    # http://www.karoltomala.com/blog/?p=679
    disp_no = os.getenv("DISPLAY")
    if disp_no:
        print "I'm running under X display = {0}".format(disp_no)

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
        raise Exception('Display init failed with driver: {0}'.format(driver))

    if xwin:
        size = (320, 200)
        options = 0
    else:
        # fullscreen
        info = pygame.display.Info()
        size = (info.current_w, info.current_h)
        print "Framebuffer size: %d x %d" % (size[0], size[1])
        options = pygame.FULLSCREEN | pygame.DOUBLEBUF
    screen = pygame.display.set_mode(size, options)

    # Clear the screen to start
    screen.fill((0, 0, 0))
    pygame.mouse.set_visible(False)
    # Render the screen
    pygame.display.update()

    return screen


def test(screen):
    img = pygame.image.load('zebrafish.png')
    imgscaled = pygame.transform.smoothscale(img, screen.get_size())
    x = time.time()
    for i in range(100):
        screen.blit(img, (0, 0))
        # Update the display
        pygame.display.flip()
        screen.blit(imgscaled, (0, 0))
        pygame.display.flip()

    print time.time()-x

# Testing
screen = get_screen(xwin=True)
test(screen)
