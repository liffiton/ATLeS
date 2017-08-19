---
title: Box Software Usage Notes
---

# Notes on Running `atles_box.py`

## Framerate

The capture framerate is sensitive to many things.

First, displaying the captured frames using highgui takes a huge amount of CPU time, making it infeasible (i.e., maxing out CPU) above 10fps.  Without displaying the images, however, CPU usage doesn't hit 100% until about 50fps.

Secondly, the capture size obviously makes a difference.  There is currently some bug in the interaction between OpenCV and V4L that makes it impossible to change the capture size after the stream is opened in OpenCV (at its default 640x480 size).  See [opencv_notes](opencv_notes.md) for directions for how to modify and compile OpenCV to fix this bug.  The fix allows us to set the video capture size smaller for better performance.  160x120 seems nice and fast, and we have lots of flexibility now.

Also, it is important to note that terminal output, displayed on the rpi's X server, uses a large amount of the CPU as well.  Simply switching to a different tab while FPS output is enabled in camtest.py drops the CPU usage significantly.  Keep this in mind particularly during testing, where debugging output may significantly harm performance.

## Exposure and white balance

Auto white balance can be disabled with:

    $ v4l2-ctl --set-ctrl=white_balance_auto_preset=1
    $ v4l2-ctl --set-ctrl=white_balance_auto_preset=0

It does seem to need to be set to 1 then back to 0 to work, at least sometimes.  Without that, AWB is somehow enabled between(?) runs, and just setting the preset to 0 at the start of the next does not work.  The set to 1 then back does work, it appears.

Exposure can be adjusted with:

    $ v4l2-ctl --set-ctrl=auto_exposure=1
    $ v4l2-ctl --set-ctrl=exposure_time_absolute=10000
    $ v4l2-ctl -p 1

"auto_exposure=1" disables auto exposure (don't ask me...).
"exposure_time_absolute" is given in multiples of 0.1ms.  It needs to be adjusted along with the frame rate (-p) so that they match.  A higher frame rate will clip the exposure to make that frame rate possible.

## Display

In X, pygame will make a fullscreen view, but it won't (as far as I've found so far) scale the image.  So if I request 640x480, I get a 640x480 surface in the middle of my monitor.

Running from the terminal, however, does work.  I don't know what interface SDL is using, exactly, but it seems alright.  It seems to only work *once*, though.  Running the program a second time results in a blank screen.  I may be using Pygame incorrectly...

