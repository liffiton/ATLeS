from bottle import post, redirect, request, route, run, static_file, view
import glob

import analyze


@route('/')
@view('index')
def index():
    tracks = glob.glob("logs/*-track.csv")
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
    run(host='localhost', port=8080, debug=True, reloader=True)
