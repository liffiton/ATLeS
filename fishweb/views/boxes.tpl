%rebase('base.tpl', title='Boxes')

<div class="container">
  <h1>Boxes</h1>

  %if not boxes:
  <div class="row">
    <div class="col-sm-6 col-sm-offset-1 text-muted">When <code>fishremote.py</code> is run on a box, it will appear here.</div>
  </div>
  %end
  <div class="row">
    %for box, info in sorted(boxes.items()):
      <div class="col-lg-4 col-sm-6">
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
              <div id="actions_{{box}}" class="row">
                <div class="col-sm-6">
                  <a href="/new/{{box}}" class="btn btn-primary" role="button">
                    <span class="glyphicon glyphicon-plus-sign"></span>
                    New Experiment
                  </a>
                </div>
                %if not info.local:
                  <div class="col-sm-6">
                    <button id="sync_button_{{box}}" type="button" class="btn btn-primary" role="button">
                      <span class="glyphicon glyphicon-refresh"></span>
                      <span class="btntxt">
                        Sync Data
                      </span>
                    </button>
                  </div>
                  </div class="col-sm-6">
                    <a href="/image/{{box}}" class="btn btn-primary" role="button">
                      <span class="glyphicon glyphicon-refresh"></span>
                      <span class="btntxt">
                        Get Image
                      </span>
                    </a>
                  </div>
                %end
              </div>
            %end
          </div>
        </div>
      </div>
    %end
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
    $("#sync_button_{{box}}").click(function(e) {
      var btn = $(this);
      var txt = $(".btntxt", this)
      var icon = $(".glyphicon-refresh", this);
      btn.attr("disabled", true);
      txt.text("Syncing...")
      icon.addClass("rotatey");
      
      $.post("/sync/{{box}}").always(function() {
        btn.attr("disabled", false);
        txt.text("Sync Data");
        icon.removeClass("rotatey");
      });
    });
    checkProgress("{{box}}", "#exp_progress_{{box}}", "#actions_{{box}}");
  %end
});
</script>
