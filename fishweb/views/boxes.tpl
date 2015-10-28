% rebase('base.tpl', hostname=None, title='Box List')

<div class="container">
  <h1>Boxes</h1>

  %if not boxes:
  <div class="row">
    <div class="col-sm-6 col-sm-offset-1 text-muted">When <code>fishremote.py</code> is run on a box, it will appear here.</div>
  </div>
  %end
  <div class="row">
    <div class="col-lg-4 col-lg-offset-1 col-md-5 col-md-offset-1 col-sm-6 col-sm-offset-2">
      %for box, info in sorted(boxes.items()):
        %if info.up:
        <div class="panel panel-success">
        %else:
        <div class="panel panel-danger">
        %end
          <div class="panel-heading">
            <h2 class="panel-title" style="font-size: x-large">{{box}}</h2>
            %if info.up:
              <b>available</b>
            %else:
              <b>down</b>
            %end
          </div>
          <div class="panel-body">
            %if info.up:
              <a href="/new/{{box}}" class="btn btn-primary" role="button">New Experiment</a>
            %end
          </div>
        </div>
      %end
    </div>
  </div>
</div>

