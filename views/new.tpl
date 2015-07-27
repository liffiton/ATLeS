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
    $("#inifile").change(function(e) {
        var iniFile = this.value;
        update_ini(iniFile);
        });
    update_ini($("#inifile option:selected").text());
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
                    <input type="checkbox" name="startFromTrigger">
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
                  <label for="stimulus">
                    <input type="radio" name="stimulus" id="stimulus" value="{{value}}">
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
