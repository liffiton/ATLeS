<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fishybox Log Analyzer/Viewer</title>
<script src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/snap.svg/0.4.1/snap.svg-min.js"></script>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
<style>
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
</style>
<script type="text/javascript">
function do_post(url, query, check) {
  if (check) {
    var go = confirm("Are you sure?  (" + check + ")");
    if (! go) return;
  }
  var form = document.createElement('form');
  form.setAttribute('method', 'post');
  form.setAttribute('action', url + "?" + query);
  form.style.display = 'hidden';
  document.body.appendChild(form)
    form.submit();
}
function async_post(url, query) {
  $.post(url + "?" + query);
}

function filter_rows(value) {
  var re = new RegExp(value);
  $("tr.log_row").each(function() {
    logfile = $(this).find(".logfile_cell").text();
    if (re.test(logfile)) {
      $(this).show();
    }
    else {
      $(this).hide();
    }
  });
  update_selection();
}

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
  makeCharts();
  makeHeatMaps();
});

function makeCharts() {
  $("svg.aml_chart").each(function() {
    var data = $(this).data("values").split('|');
    var acquired = parseFloat(data[0]);
    var missing = parseFloat(data[1]);
    var lost = parseFloat(data[2]);
    var a = acquired;
    var b = missing;
    var c = lost;

    var s = Snap(this);
    s.group(
      // Chrome requires the title tag to be in a group with the graphics
      // elements (not just part of the <svg> itself) to display it as a tooltip.
      Snap.parse("<title>" + this.getAttribute('title') + "</title>"),
      s.rect(0,0,a,1).attr({fill: '#0d0'}),
      s.rect(a,0,b,1).attr({fill: '#fc0'}),
      s.rect(a+b,0,c,1).attr({fill: '#d00'})
    );
  });
}

function makeHeatMaps() {
  // number of buckets we're receiving and plotting
  var _width = 15;
  var _height = 10;

  $("svg.heatmap").each(function() {
    var data = $(this).data("values").split('|');

    var s = Snap(this);
    // background
    s.rect(0,0,15,10).attr({fill: Snap.rgb(240,240,240)});

    for (var i = 0 ; i < data.length ; i++) {
      point = data[i].split(',');
      var x = parseFloat(point[0])*_width;
      var y = parseFloat(point[1])*_height;
      var amt = parseFloat(point[2]);
      amt = Math.sqrt(amt);  // scale so lower values are more intense/visible
      color = Snap.rgb(240-240*amt, 240-200*amt, 240-120*amt);
      s.rect(x, _height-1-y, 1, 1).attr({fill: color})
    }
  });
}

// keep track of selected tracks
var selection = Object.create(null);  // an empty object to be used as a set
function sel_count() {
  return Object.keys(selection).length;
}
function togglesel(row) {
  var sel_button = $(row).find(".selectbutton");
  sel_button.toggleClass('btn-primary');
  update_selection();
}
function toggle_select_all() {
  var log_rows = $("tr.log_row").filter(":visible");
  var row_count = log_rows.length;
  var notall = (sel_count() < row_count);
  log_rows.each(function() {
    var sel_button = $(this).find(".selectbutton");
    if (notall != sel_button.hasClass('btn-primary')) {
      togglesel(this);
    }
  });
}
function update_selection() {
  selection = Object.create(null);  // reset
  var log_rows = $("tr.log_row").filter(":visible");
  log_rows.each(function() {
    var path = $(this).data('path');
    var sel_button = $(this).find(".selectbutton");
    if (sel_button.hasClass('btn-primary')) {
      // add to the set
      selection[path] = true;
    }
  });
  update_buttons();
}
function update_buttons() {
  var count = sel_count();
  var log_rows = $("tr.log_row").filter(":visible");
  var row_count = log_rows.length;
  $('#comparebutton').toggleClass('disabled', count != 2);
  $('#comparebutton').toggleClass('btn-primary', count == 2);
  $('#statsbutton').toggleClass('disabled', count == 0);
  $('#statsbutton').toggleClass('btn-primary', count > 0);
  $('#statscsvbutton').toggleClass('disabled', count == 0);
  $('#statscsvbutton').toggleClass('btn-primary', count > 0);
  $('#selectallbutton').toggleClass('btn-default', count < row_count);
  $('#selectallbutton').toggleClass('btn-primary', count == row_count);
}

function do_compare() {
  var sels = Object.keys(selection).sort();
  do_post('/compare/', 'p1=' + sels[0] + '&p2=' + sels[1]);
}

function do_stats() {
  var sels = Object.keys(selection).sort();
  do_post('/stats/', 'logs=' + sels.join('|'));
}

function do_stats_csv() {
  var sels = Object.keys(selection).sort();
  do_post('/stats/', 'csv=true&logs=' + sels.join('|'));
}

function do_archive(path, index) {
  async_post('/archive/', 'path=' + path);
  $("#row_" + index + "_undo").show();
  $("#row_" + index).hide();
}

function do_unarchive(path, index) {
  async_post('/unarchive/', 'path=' + path);
  $("#row_" + index).show();
  $("#row_" + index + "_undo").hide();
}
</script>
</head>
<body>
<div class="container">
  <div class="row">
    <div class="col-lg-10 col-md-12 col-sm-12">
      <h1>
        <a class="btn btn-primary pull-right" href="/new/">
          <span class="glyphicon glyphicon-plus-sign"></span>
          Start New Experiment
        </a>
        <span>Fishybox Log Analyzer/Viewer</span>
      </h1>
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
        </p>
        <p>
        Global actions:
        <button type="button" class="btn btn-default" title="Re-analyze All" onclick="do_post('/analyze_all/', null, 'This will take a long time with no feedback while running.');">
          <span class="glyphicon glyphicon-refresh"></span>
          All
        </button>
        </p>
      </div>
    </div>
  </div>

</div>
</body>
</html>
