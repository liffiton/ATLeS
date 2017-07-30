from pathlib import Path

# base directory is parent of directory holding this config script
BASEDIR = Path(__file__).resolve().parent.parent

DATADIR = BASEDIR / "data"
DBFILE      = DATADIR / "atles.db"
LOCKFILE    = DATADIR / "current_experiment.lock"
TRACKDIR    = DATADIR / "tracks"
PLOTDIR     = DATADIR / "plots"
ARCHIVEDIR  = DATADIR / "tracks_archive"
DBGFRAMEDIR = DATADIR / "debug_frames"

INIDIR = BASEDIR / "ini"

EXPSCRIPT = BASEDIR / "src" / "fishbox.py"

WEBAPPDIR = BASEDIR / "src" / "fishweb"
TEMPLATEDIR = WEBAPPDIR / "views"
STATICDIR   = WEBAPPDIR / "static"
IMGDIR      = STATICDIR / "bgimgs"

# Options used by software running on remotes (boxes)
FISHREMOTE_USER = "pi"  # username for logging into this Pi via SSH
HAS_DISPLAY = False  # does this Pi have a display attached for "background" images
