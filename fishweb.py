from bottle import post, redirect, request, route, run, static_file, view
import glob

# Import matplotlib ourselves and make it use agg (not any GUI anything)
# before the analyze module pulls it in.
import matplotlib
matplotlib.use('Agg')

import analyze


@route('/')
@view('index')
def index():
    tracks = glob.glob("logs/*-track.csv")
    tracks.sort()
    img_counts = []
    for track in tracks:
        name = track.split('/')[-1]
        imgs = glob.glob("logs/img/%s*" % name)
        img_counts.append(len(imgs))
    return dict(tracks=zip(tracks, img_counts))


@route('/view/<logname:path>')
@view('view')
def view(logname):
    name = logname.split('/')[-1]
    imgs = glob.glob("logs/img/%s*" % name)
    imgs.sort()
    return dict(imgs=imgs)


@post('/analyze/')
def do_analyze():
    logname = request.query.path
    name = logname.split('/')[-1]
    g = analyze.Grapher()
    g.load(logname)
    g.plot()
    g.savefig("logs/img/%s.plot.png" % name)
    g.plot_heatmap()
    g.savefig("logs/img/%s.heat.png" % name)
    g.plot_heatmap(10)
    g.savefig("logs/img/%s.heat.10.png" % name)

    redirect("/view/%s" % logname)


@route('/logs/<filename:path>')
def static_logs(filename):
    return static_file(filename, root='logs/')


if __name__ == '__main__':
    run(host='0.0.0.0', port=8080, debug=True, reloader=True)
