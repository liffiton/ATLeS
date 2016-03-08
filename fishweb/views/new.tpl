%rebase('base.tpl', title='New Experiment on %s' % box)

<div class="container">
  <h1>New Experiment on <span class="hostname">{{box}}</span></h1>

  <div class="exp_progress_box row" id="exp_progress">
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
      <form id="new_exp_form" class="form-horizontal" action="/new/{{box}}" method="post">
        <div class="panel panel-default" id="experiment_form">
          <div class="panel-heading">
            <h3 class="panel-title">Experiment Setup</h3>
          </div>
          <div class="panel-body">
            %if form.errors:
            <div class="row">
              <div class="col-sm-12">
                <div class="alert alert-danger">
                  Form entries contain errors.  See below.
                  <!-- {{form.errors}} -->
                </div>
              </div>
            </div>
            %end
            <div class="form-group {{"has-error" if form.expname.errors else ""}}">
              {{!form.expname.label(class_="col-sm-4 control-label")}}
              <div class="col-sm-8">
                {{!form.expname(class_="form-control")}}
                %if form.expname.errors:
                  %for e in form.expname.errors:
                    <p class="help-block">{{e}}</p>
                  %end
                %end
              </div>
            </div>
            <div class="form-group {{"has-error" if form.inifile.errors else ""}}">
              {{!form.inifile.label(class_="col-sm-4 control-label")}}
              <div class="col-sm-8">
                {{!form.inifile(class_="form-control")}}
              </div>
              %if form.inifile.errors:
                %for e in form.inifile.errors:
                  <p class="help-block">{{e}}</p>
                %end
              %end
            </div>
            <div class="form-group">
              <label class="col-sm-4 control-label" for="phasecount"># Phases</label>
              <div class="col-sm-3">
                <div class="input-group">
                  <span class="input-group-btn">
                    <button type="button" class="btn btn-default" id="btn_delPhase">-</button>
                  </span>
                  <input class="form-control" id="phasecount" name="phasecount" type="text" readonly>
                  <span class="input-group-btn">
                    <button type="button" class="btn btn-default" id="btn_addPhase">+</button>
                  </span>
                </div>
              </div>
            </div>
            <table class="table table-hover table-vertmid">
              <thead>
                <tr>
                  <th>
                    Phase
                  </th>
                  <th>
                    Length
                  </th>
                  <th>
                    Conditional Stimulus
                  </th>
                </tr>
              </thead>
              <tbody>
                %for i, phase in enumerate(form.phases):
                  <tr class="phasediv {{'hidden' if not phase.enabled.data else ''}}" id="phase_{{i}}">
                    <th class="text-center">
                      {{!phase.enabled(class_="hidden", id="var_enabled")}}
                      {{i+1}}
                    </th>
                    <td class="{{"has-error" if phase.length.errors else ""}}" width="30%">
                      <div class="input-group col-sm-11">
                        {{!phase.length(class_="form-control")}}
                        <span class="input-group-addon">
                          minutes
                        </span>
                      </div>
                      %if phase.length.errors:
                        %for e in phase.length.errors:
                          <div class="help-block">{{e}}</div>
                        %end
                      %end
                    </td>
                    <td class="radio {{"has-error" if phase.stimulus.errors else ""}}">
                      %for value, label, _ in phase.stimulus.iter_choices():
                        <label class="radio-inline" for="{{phase.stimulus.name}}:{{value}}">
                          <input type="radio" name="{{phase.stimulus.name}}" id="{{phase.stimulus.name}}:{{value}}" value="{{value}}">
                          {{label}}
                        </label>
                      %end
                      %if phase.stimulus.errors:
                        %for e in phase.stimulus.errors:
                          <div class="help-block">{{e}}</div>
                        %end
                      %end
                    </td>
                  </tr>
                  %end
              </tbody>
            </table>
            <div class="form-group">
              <div class="col-sm-8 col-sm-offset-4">
                <button type="submit" class="btn btn-primary">Start</button>
                &nbsp;
                <button type="reset" class="btn btn-sm">Reset Form</button>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>

    <div class="col-lg-6 col-md-8 col-sm-10">
      <!-- Camera view -->
      <div class="panel panel-default" id="experiment_form">
        <div class="panel-heading">
          <h3 class="panel-title">Current Camera View</h3>
        </div>
        <div class="panel-body">
          <img class="center-block" src="/image/{{box}}/324" width=324 height=243>
        </div>
      </div>

      <!-- .ini file display -->
      <div class="panel panel-info" id="inidisplay">
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
  $("#inifile").on("change reset", function(e) {
    var iniFile = this.value;
    update_ini(iniFile);
  });

  $("#clear_exp_button").click(function(e) {
    var go = confirm("Are you sure?  (Any running experiment will be terminated.)");
    if (! go) return;
    $.post("/clear_experiment/{{box}}");
  });

  // for handling dynamic form
  $("#btn_addPhase").click(add_phase);
  $("#btn_delPhase").click(del_phase);

  // store and load values used in forms
  $.each($("form"), load_form_data);
  $("form").submit(save_form_data);
  // and clear anything we've saved if the user resets the form
  $("form *").filter(":reset").click(clear_form_data);
  // and reset the phases
  $("form").on("reset", function() {
    setTimeout(update_phase_ui, 0);
  });

  // Update UI after everything is setup
  checkProgress("{{box}}");
  update_phase_ui();
  update_ini($("#inifile option:selected").text());
});
</script>
