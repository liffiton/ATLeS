DATADIR = "data/"
DBFILE = DATADIR + "fishweb.db"
TRACKDIR = DATADIR + "tracks/"
LOCKFILE = DATADIR + "current_experiment.lock"
PLOTDIR = DATADIR + "plots/"
ARCHIVEDIR = DATADIR + "tracks_archive/"
DBGFRAMEDIR = DATADIR + "debug_frames/"

INIDIR = "ini/"

EXPSCRIPT = "python fishbox.py"

WEBAPPDIR = "fishweb/"
TEMPLATEDIR = WEBAPPDIR + "views/"
STATICDIR = WEBAPPDIR + "static/"
IMGDIR = STATICDIR + "bgimgs/"

FISHREMOTE_USER = "pi"  # username for logging into remote Pi via SSH

HAS_DISPLAY = False  # does the Pi have a display attached for "background" images
