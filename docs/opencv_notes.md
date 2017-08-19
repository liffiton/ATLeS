Installing an Updated OpenCV on the Raspbery Pi
===============================================

The following instructions assume an updated Raspbian system.

Based on [OpenCV Linux Install][].

[To build/install on Cygwin, see [OpenCV Cygwin Install][].]

[OpenCV Linux Install]: http://docs.opencv.org/doc/tutorials/introduction/linux_install/linux_install.html
[OpenCV Cygwin Install]: http://hvrl.ics.keio.ac.jp/kimura/opencv/


Build dependencies
------------------

Packages that need to be installed in addition to the defaults.  [There may be
something missing here that isn't included in the default Raspbian install, but
this is what I had to add to my current setup.]

```
cmake
libgtk2.0-dev
python3-dev
libavcodec-dev
libavformat-dev
libswscale-dev
libpng12-dev
libjasper-dev
libtiff-dev
```

To install these:

    $ sudo apt-get install cmake libgtk2.0-dev python3-dev libavcodec-dev libavformat-dev libswscale-dev libpng12-dev libjasper-dev libtiff-dev

Download OpenCV
---------------

ATLeS currently works and has been tested with OpenCV 3.2.0.  You can download
this release from [OpenCV's Releases page](http://opencv.org/releases.html).
ATLeS may work with earlier versions, but compatibility is not guaranteed.

Build instructions
------------------

In the opencv-3.2.0 directory, run:

```sh
$ mkdir release
$ cd release
$ cmake -D CMAKE_BUILD_TYPE=RELEASE -D CMAKE_INSTALL_PREFIX=/usr/local -D BUILD_EXAMPLES=off -D BUILD_TESTS=off -D BUILD_PERF_TESTS=off ..
```

In the output of cmake, verify that "OpenCV modules">"To be built" lists
python, "GUI" has "YES" for GTK+, and the "Python" section lists correct paths
to binaries/libraries.  Tests, examples, and performance tests are not built to
save space.  It takes far too much space with those enabled (I ran out of space
with 1.1GB free to start).

    $ make

This step, building OpenCV with the above configuration, takes about 4 hours on
the RPi B+.

    $ sudo make install

The easiest way to check the installation now is to launch the python
interpreter and type `import cv2`.  If it does not report an error when
importing the module, the installation is probably complete.
