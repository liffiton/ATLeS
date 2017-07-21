import os

DATADIR = "data/"
DBFILE      = os.path.join(DATADIR, "atles.db")
LOCKFILE    = os.path.join(DATADIR, "current_experiment.lock")
TRACKDIR    = os.path.join(DATADIR, "tracks/")
PLOTDIR     = os.path.join(DATADIR, "plots/")
ARCHIVEDIR  = os.path.join(DATADIR, "tracks_archive/")
DBGFRAMEDIR = os.path.join(DATADIR, "debug_frames/")

INIDIR = "ini/"

EXPSCRIPT = "./fishbox.py"

WEBAPPDIR = "fishweb/"
TEMPLATEDIR = os.path.join(WEBAPPDIR, "views/")
STATICDIR   = os.path.join(WEBAPPDIR, "static/")
IMGDIR      = os.path.join(STATICDIR, "bgimgs/")

# Options used by software running on remotes (boxes)
FISHREMOTE_USER = "pi"  # username for logging into this Pi via SSH
HAS_DISPLAY = False  # does this Pi have a display attached for "background" images
