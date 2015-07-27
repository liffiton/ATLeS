<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fishybox: Start New Experiment</title>
<script src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
<style>
div#inidisplay {
  display: none;
}
pre#inidisplay_contents {
  max-height: 30em;
}
</style>
<script type="text/javascript">
function update_ini(iniFile) {
  $.get("/" + iniFile, function(data) {
      lines = data.split('\n');
      real_lines = lines.filter(function(line) {return line[0] != '#';});
      contents = real_lines.join('\n').replace("\n", "");
      $("#inidisplay_name").text(iniFile);
      $("#inidisplay_contents").text(contents);
      $("#inidisplay").show();
      });
}
$(function() {
    $("#sel_iniFile").change(function(e) {
        var iniFile = this.value;
        update_ini(iniFile);
        });
    update_ini($("#sel_iniFile option:selected").text());
    });
</script>
</head>
<body>
<div class="container">
  <h1>Fishybox: Start New Experiment</h1>

  <div class="row">
    <div class="col-lg-6 col-md-8 col-sm-10">
      <form class="form-horizontal" action="/create/" method="post">
        <div class="panel panel-default" id="experiment_form">
          <div class="panel-heading">
            <h3 class="panel-title">Experiment Setup</h3>
          </div>
          <div class="panel-body">
            <div class="form-group">
              <label for="experimentName" class="col-sm-4 control-label">Experiment Name</label>
              <div class="col-sm-8">
                <input type="text" class="form-control" name="experimentName">
              </div>
            </div>
            <div class="form-group">
              <label for="timeLimit" class="col-sm-4 control-label">Time Limit</label>
              <div class="col-sm-8">
                <div class="input-group col-sm-5">
                  <input type="text" class="form-control" name="timeLimit">
                  <span class="input-group-addon">
                    minutes
                  </span>
                </div>
                <div class="checkbox">
                  <label>
                    <input type="checkbox" name="startFromTrigger">
                    Start timing from first trigger
                  </label>
                </div>
              </div>
            </div>
            <div class="form-group">
              <label class="col-sm-4 control-label">Stimulus</label>
              <div class="col-sm-8">
                <div class="radio">
                  <label>
                    <input type="radio" name="stimulus" value="nostim">
                    Off
                  </label>
                </div>
                <div class="radio">
                  <label>
                    <input type="radio" name="stimulus" value="stim">
                    On
                  </label>
                </div>
                <div class="radio">
                  <label>
                    <input type="radio" name="stimulus" value="randstim">
                    Randomized (equal chance off or on)
                  </label>
                </div>
              </div>
            </div>
            <div class="form-group">
              <label for="iniFile" class="col-sm-4 control-label">.ini File</label>
              <div class="col-sm-8">
                <select class="form-control" name="iniFile" id="sel_iniFile">
                  %for file in inifiles:
                    <option>{{file}}</option>
                  %end
                </select>
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
</body>
</html>