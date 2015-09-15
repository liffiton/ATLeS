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
function async_post(url, query, check, success) {
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

function updateProgress(data) {
  $("#exp_run_since").text(data["starttimestr"]);

  var start = parseInt(data["starttime"])*1000;
  var runtime = parseInt(data["runtime"])*1000;
  var startdate = new Date(start);
  var curdate = new Date();
  var millis_gone = curdate.getTime() - startdate.getTime();
  var millis_remaining = (startdate.getTime() + runtime) - curdate.getTime();

  var barwidth = Math.min(100, 100 * millis_gone / runtime);
  $("#exp_progressbar").width(barwidth + "%");

  var min_remaining = Math.round(millis_remaining / 1000 / 60);
  var remtext = min_remaining + " min remaining";
  if (barwidth < 50) {
    $("#rem_in").html("");
    $("#rem_out").html(remtext);
  }
  else {
    $("#rem_in").html(remtext);
    $("#rem_out").html("");
  }
}

function checkProgress() {
  $.get('/lock_data/').success(function(data) {
    if (data == '') {
      $("#exp_progress").hide();
      $("#new_exp_button").show();
    }
    else {
      updateProgress(data);
      $("#exp_progress").show();
      $("#new_exp_button").hide();
    }
  });
  window.setTimeout(checkProgress, 5000);
}

function makeCharts() {
  $("svg.aml_chart").each(function() {
    var rawdata = $(this).data("values");
    if (rawdata == "") {
      return;
    }
    var data = rawdata.split('|');
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
  $('#replotselbutton').toggleClass('disabled', count == 0);
  $('#replotselbutton').toggleClass('btn-primary', count > 0);
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

function analyze_selection() {
  var go = confirm("This operation will run in the background with no feedback while running or when complete (sorry).");
  if (! go) return;
  var sels = Object.keys(selection).sort();
  async_post('/analyze_selection/', 'selection=' + sels.join('|'));
}

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
