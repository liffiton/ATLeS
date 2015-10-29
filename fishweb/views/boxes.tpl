%rebase('base.tpl', box=None, title='Box List')

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
        %if info.status == "connected":
        <div class="panel panel-success">
        %else:
        <div class="panel panel-danger">
        %end
          <div class="panel-heading">
            <h2 class="panel-title" style="font-size: x-large">{{box}}</h2>
            {{info.status}}
          </div>
          <div class="panel-body">
            %if info.status == "connected":
              <div id="exp_progress_{{box}}" class="alert alert-info small">
                <button id="clear_exp_button_{{box}}" type="button" class="btn btn-danger btn-xs pull-right" title="Kill experiment">
                  <span class="glyphicon glyphicon-remove"></span>
                </button>
                <strong>Experiment running</strong> since <span id="exp_run_since"></span>.
                <div class="progress" style="width: 90%;">
                  <div id="exp_progressbar" class="progress-bar progress-bar-striped" role="progressbar" style="width: 0%;">
                    <span class="pull-right" id="rem_in"></span>
                  </div>
                  <span class="pull-right" id="rem_out"></span>
                </div>
              </div>
              <div id="actions_{{box}}">
                <a href="/new/{{box}}" class="btn btn-primary" role="button">
                  <span class="glyphicon glyphicon-plus-sign"></span>
                  New Experiment
                </a>
                %if not info.local:
                  <form class="form-inline" role="form" method="post" action="/sync/{{box}}">
                    <button type="submit" class="btn btn-primary" role="button">
                      <span class="glyphicon glyphicon-download-alt"></span>
                      Sync Data
                    </button>
                  </form>
                %end
              </div>
            %end
          </div>
        </div>
      %end
    </div>
  </div>
</div>

<script type="text/javascript">
// setup handlers / onload stuff
$(function() {
  %for box, info in sorted(boxes.items()):
    $("#clear_exp_button_{{box}}").click(function(e) {
      var go = confirm("Are you sure?  (The running experiment will be terminated.)");
      if (! go) return;
      $.post("/clear_experiment/{{box}}");
    });
    checkProgress("{{box}}", "#exp_progress_{{box}}", "#actions_{{box}}");
  %end
});
</script>
