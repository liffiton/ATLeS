%rebase('base.tpl', title='New Experiment on %s' % box)

<div class="container">
  <h1>New Experiment on <span class="hostname">{{box}}</span></h1>

  <div class="row" id="exp_progress">
    <div class="col-sm-6 col-sm-offset-1 alert alert-info">
      <strong>Experiment running</strong> since <span id="exp_run_since"></span>.
      <div class="progress" style="width: 100%;">
        <div id="exp_progressbar" class="progress-bar progress-bar-striped" role="progressbar" style="width: 0%;">
          <span class="pull-right" id="rem_in"></span>
        </div>
        <span class="pull-right" id="rem_out"></span>
      </div>
    </div>
    <div class="col-sm-4 col-sm-offset-1 alert alert-danger">
      <p>Due to an existing lockfile, it looks like an experiment is already running on this box.  Only one experiment can run at a time.</p>
      <p>You may override this (ending any running experiment and deleting the lockfile) if you really want to:</p>
      <p>
        <button type="button" class="btn btn-danger" id="clear_exp_button">
          <span class="glyphicon glyphicon-fire"></span>
          Clear experiment
          <span class="glyphicon glyphicon-fire"></span>
        </button>
      </p>
    </div>
  </div>

  <div class="row" id="exp_new">
    <div class="col-lg-6 col-md-8 col-sm-10">
      <form class="form-horizontal" action="/create/{{box}}" method="post">
        <div class="panel panel-default" id="experiment_form">
          <div class="panel-heading">
            <h3 class="panel-title">Experiment Setup</h3>
          </div>
          <div class="panel-body">
            %if form.errors:
            <div class="row">
              <div class="col-sm-12">
                <div class="alert alert-danger">
                  %for field, errors in form.errors.iteritems():
                    <p><strong>{{!form[field].label}}:</strong> {{' - '.join(errors)}}</p>
                  %end
                </div>
              </div>
            </div>
            %end
            <div class="form-group">
              {{!form.expname.label(class_="col-sm-4 control-label")}}
              <div class="col-sm-8">
                {{!form.expname(class_="form-control")}}
              </div>
            </div>
            <div class="form-group">
              {{!form.timelimit.label(class_="col-sm-4 control-label")}}
              <div class="col-sm-8">
                <div class="input-group col-sm-5">
                  {{!form.timelimit(class_="form-control")}}
                  <span class="input-group-addon">
                    minutes
                  </span>
                </div>
                <div class="checkbox">
                  <label>
                    {{!form.startfromtrig}}
                    Start timing from first trigger
                  </label>
                </div>
              </div>
            </div>
            <div class="form-group">
              {{!form.stimulus.label(class_="col-sm-4 control-label")}}
              <div class="col-sm-8">
                %for value, label, _ in form.stimulus.iter_choices():
                <div class="radio">
                  <label for="stimulus:{{value}}">
                    <input type="radio" name="stimulus" id="stimulus:{{value}}" value="{{value}}">
                    {{label}}
                  </label>
                </div>
              %end
              </div>
            </div>
            <div class="form-group">
              {{!form.inifile.label(class_="col-sm-4 control-label")}}
              <div class="col-sm-8">
                {{!form.inifile(class_="form-control")}}
              </div>
            </div>
            <div class="form-group">
              <div class="col-sm-8 col-sm-offset-4">
                <button type="submit" class="btn btn-primary">Start</button>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
    <div class="col-lg-6 col-md-8 col-sm-10" id="inidisplay">
      <div class="panel panel-info">
        <div class="panel-heading">
          <h3 class="panel-title" id="inidisplay_name"></h3>
        </div>
        <div class="panel-body small">
          <pre id="inidisplay_contents">
          </pre>
          <i>Note: comments have been stripped.</i>
        </div>
      </div>
    </div>
  </div>

</div>

<script type="text/javascript">
$(function() {
  $("#inifile").change(function(e) {
    var iniFile = this.value;
    update_ini(iniFile);
  });
  update_ini($("#inifile option:selected").text());

  $("#clear_exp_button").click(function(e) {
    var go = confirm("Are you sure?  (Any running experiment will be terminated.)");
    if (! go) return;
    $.post("/clear_experiment/");
  });
  checkProgress("{{box}}");
});
</script>
