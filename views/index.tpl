<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fishybox Log Analyzer/Viewer</title>
<script src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/snap.svg/0.4.1/snap.svg-min.js"></script>
<script src="/static/fishweb.js"></script>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
<style>
div.my-header {
  padding-top: 1em;
  border-bottom: 2px solid #ddd;
}
div#exp_progress {
  padding: 0.5em;
  margin-bottom: 0.5em;
  display: none;  /* hidden by default */
}
tr.undo_row {
  display: none;  /* default, will be overridden to display */
  color: #999999;
  background: #eeeeee;
}
td.actionbuttons {
  white-space: nowrap;  /* keep all buttons on one line */
}
input#rowfilter {
  font-weight: normal;
  margin-left: 2em;
  padding: 0 0.5em;
  border-radius: 10em;
  border: solid 1px #ccc;
  box-shadow: 1px 1px 2px 1px #ccc;
}
span#filterclear {
  position: relative;
  left: -1.2em;
  top: -0.1em;
  color: #999;
  cursor: pointer;
}
body {
  overflow-y: scroll;  /* Scroll bar always present -- avoids bouncing on hide/show of rows */
}
.number_cell {
  text-align: right;
}
.svg_cell {
  vertical-align: middle;
  position: relative;
}
svg.aml_chart {
  width: 4em;
  height: 1em;
  /* centering */
  position: absolute;
  top: 50%;
  left: 50%;
  margin-left: -2em;  /* half width */
  margin-top: -0.5em;  /* half height */
}
svg.heatmap {
  width: 3em;
  height: 2em;
  /* centering */
  position: absolute;
  top: 50%;
  left: 50%;
  margin-left: -1.5em;  /* half width */
  margin-top: -1em;  /* half height */
}
.alert .progress {
  margin-bottom: 0;
}
#rem_in, #rem_out {
  padding-right: 0.3em;
}
</style>
<script type="text/javascript">
// setup handlers / onload stuff
$(function() {
  $("#filterclear").click(function(e) {
    $("#rowfilter").val('');
    $("#rowfilter").trigger('input');
  });
  $("#rowfilter").on('input', function(e) {
    filter_rows(this.value);
  });
  $("#selectallbutton").click(toggle_select_all);
  $("tr.log_row .selectbutton").click(function(e) {
    var row = $(this).closest("tr");
    togglesel(row);
  });
  $("#clear_exp_button").click(function(e) {
    var go = confirm("Are you sure?  (Any running experiment will be terminated.)");
    if (! go) return;
    $.post("/clear_experiment/")
      .always(checkProgress);
  });
  makeCharts();
  makeHeatMaps();
  checkProgress();
});
</script>
</head>
<body>
<div class="container">
  <div class="row">
    <div class="my-header col-lg-10 col-md-12 col-sm-12">
      <div id="header_right" class="col-sm-6 col-md-5 col-lg-4 pull-right">
        <div id="exp_progress" class="alert alert-info small">
          <button id="clear_exp_button" type="button" class="btn btn-danger btn-xs pull-right" title="Kill experiment">
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
        <div id="new_exp_button" class="pull-right">
          <a class="btn btn-primary" href="/new/">
            <span class="glyphicon glyphicon-plus-sign"></span>
            Start New Experiment
          </a>
        </div>
      </div>
      <span class="h1">
        Fishybox Log Analyzer/Viewer
      </span>
    </div>
  </div>
  <div class="row">
    <div class="col-lg-10 col-md-12 col-sm-12">
      <table class="table table-hover">
        <thead>
          <tr>
            <th>
              <button type="button" class="btn btn-default btn-xs text-muted" id="selectallbutton" title='Select All'>
                <span class="glyphicon glyphicon-ok"></span>
              </button>
            </th>
            <th width="100%">Log file <input type="search" placeholder="filter rows" id="rowfilter"><span id="filterclear">x</span></th>
            <th class="number_cell">Points</th>
            <th class="svg_cell"><acronym title="Acquired/Missing/Lost">A/M/L</acronym></th>
            <th class="svg_cell">Position heatmap</th>
            <th>Plots</th>
            <th>Actions</th>
          </tr>
        </thead>
        %for index, path, points, aml, heat, img_count in tracks:
        <tr class="undo_row" id="row_{{index}}_undo">
          <td></td>
          <td>{{path}}</td>
          <td colspan=4><i>Archived</i></td>
          <td>
            <button type="button" class="btn btn-xs btn-warning" onclick="do_unarchive('{{path}}', {{index}});" title="Unarchive">
              <span class="glyphicon glyphicon-log-in"></span>
              Undo archive
            </button>
          </td>
        </tr>
        <tr class="log_row" id="row_{{index}}" data-path='{{path}}'>
          <td>
            <button type="button" class="btn btn-default btn-xs text-muted selectbutton" title='Select'>
              <span class="glyphicon glyphicon-ok"></span>
            </button>
          </td>
          <td class="logfile_cell"><a href="/{{path}}">{{path}}</a></td>
          <td class="number_cell">{{points}}</td>
          <td class="svg_cell">
            <svg class="aml_chart" viewbox="0 0 1 0.1" data-values="{{'|'.join(aml)}}" title="{{' / '.join(aml)}}" preserveAspectRatio="none"></svg>
          </td>
          <td class="svg_cell">
            %if heat:
            <svg class="heatmap" viewbox="0 0 15 10" data-values="{{'|'.join(','.join(item) for item in heat)}}" title="Position heatmap" preserveAspectRatio="none"></svg>
            %end
          </td>
          <td>
            %if img_count:
            <a href="/view/{{path}}">View</a>
            %end
          </td>
          <td class="actionbuttons">
            %if points > 0:
            <button type="button" class="btn btn-default btn-xs" onclick="do_post('/analyze/', 'path={{path}}');">
              %if img_count:
              <span class="glyphicon glyphicon-refresh"></span>
              Re-plot
              %else:
              <span class="glyphicon glyphicon-plus"></span>
              Plot
              %end
            </button>
            %end
            <button type="button" class="btn btn-xs btn-danger" onclick="do_archive('{{path}}', {{index}});" title='Archive'>
              <span class="glyphicon glyphicon-log-out"></span>
            </button>
          </td>
        </tr>
        %end
      </table>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-6 col-md-8 col-sm-10">
      <div class="well">
        <p>
        With selection:
        <button type="button" class="btn btn-default disabled" id="comparebutton" onclick="do_compare();">
          Compare
        </button>
        <button type="button" class="btn btn-default disabled" id="statsbutton" onclick="do_stats();">
          View Statistics
        </button>
        <button type="button" class="btn btn-default disabled" id="statscsvbutton" onclick="do_stats_csv();">
          Download Statistics (CSV)
        </button>
        <button type="button" class="btn btn-default disabled" title="Re-plot" id="replotselbutton" onclick="analyze_selection();">
          <span class="glyphicon glyphicon-refresh"></span>
          Re-plot
        </button>
        </p>
      </div>
    </div>
  </div>

</div>
</body>
</html>
