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
  $("tr.track_row").each(function() {
    trackfile = $(this).find(".trackfile_cell").text();
    if (re.test(trackfile)) {
      $(this).show();
    }
    else {
      $(this).hide();
    }
  });
  update_selection();
}

function updateProgress(data, progdiv) {
  progdiv.find("#exp_run_since").text(data.starttimestr);

  var start = parseInt(data["starttime"])*1000;
  var runtime = parseInt(data["runtime"])*1000;
  var startdate = new Date(start);
  var curdate = new Date();
  var millis_gone = curdate.getTime() - startdate.getTime();
  var millis_remaining = (startdate.getTime() + runtime) - curdate.getTime();

  var barwidth = Math.min(100, 100 * millis_gone / runtime);
  progdiv.find(".progress-bar").width(barwidth + "%");

  if (millis_remaining < 60*1000) {
    var sec_remaining = Math.round(millis_remaining / 1000);
    var remtext = sec_remaining + " sec remaining";
  }
  else {
    var min_remaining = Math.round(millis_remaining / 1000 / 60);
    var remtext = min_remaining + " min remaining";
  }
  if (barwidth < 50) {
    progdiv.find("#rem_in").html("");
    progdiv.find("#rem_out").html(remtext);
  }
  else {
    progdiv.find("#rem_in").html(remtext);
    progdiv.find("#rem_out").html("");
  }
}

function checkProgress(boxname, progress_id, new_id) {
  if (typeof(boxname)==='undefined') boxname = ""
  if (typeof(progress_id)==='undefined') progress_id = "#exp_progress"
  if (typeof(new_id)==='undefined') new_id = "#exp_new"
  $.get('/lock_data/' + boxname).done(function(data) {
    if (data['running']) {
      updateProgress(data, $(progress_id));
      $(progress_id).show();
      $(new_id).hide();
    }
    else {
      $(progress_id).hide();
      $(new_id).show();
    }
  }).always(function() {
    window.setTimeout(checkProgress, 2000, boxname, progress_id, new_id);
  });
}

function makeAML() {
    // configuration: number of drawing pixels for bar chart
    var _width = 500;

    var values = $(this).data("values");
    if (!values) return;

    var data = values.split('|');
    var acquired = parseFloat(data[0]);
    var missing = parseFloat(data[1]);
    var lost = parseFloat(data[2]);
    var a = acquired * _width;
    var b = missing * _width;
    var c = lost * _width;

    this.width = _width;
    this.height = 1;
    var ctx = this.getContext("2d");

    ctx.fillStyle = "#0d0";
    ctx.fillRect(0,0,a,1);
    ctx.fillStyle = "#fc0";
    ctx.fillRect(a,0,b,1);
    ctx.fillStyle = "#d00";
    ctx.fillRect(a+b,0,c,1);
}

function makeHeatMap() {
    var data = $(this).data("values").split('|');

    // get number of buckets from received data
    var _width = data[0].split(',').length;
    var _height = data.length;

    this.width = _width;
    this.height = _height;
    var ctx = this.getContext("2d");

    // background
    ctx.fillStyle = "rgb(240,240,240)";
    ctx.fillRect(0,0,_width,_height);

    for (var y = 0 ; y < _height ; y++) {
        var rowdata = data[y].split(',');
        for (var x = 0 ; x < _width ; x++) {
            var amt = parseInt(rowdata[x]) / 1000;
            amt = Math.sqrt(amt);
            var r = Math.floor(240-240*amt);
            var g = Math.floor(240-200*amt);
            var b = Math.floor(240-120*amt);
            ctx.fillStyle = "rgb(" + r + "," + g + "," + b + ")";
            ctx.fillRect(x, (_height-1)-y, 1, 1);
        }
    }
}

function makeVelocityPlot() {
    // configuration: number of buckets (x) we'll put velocities into
    var _width = 100;

    var values = $(this).data("values");
    if (!values) return;
    values = values.split(',');
    var avg = values[0];
    var max = values[1];

    // scale so small values stand out more
    avg = Math.sqrt(parseFloat(avg));
    max = Math.sqrt(parseFloat(max));

    this.width = _width;
    this.height = 1;
    var ctx = this.getContext("2d");

    // background
    ctx.fillStyle = "rgb(240,240,240)";
    ctx.fillRect(0,0,_width, 1);

    ctx.fillStyle = "rgb(40,240,40)";
    ctx.fillRect((_width-1) * avg, 0, 1, 1);

    ctx.fillStyle = "rgb(240,120,40)";
    ctx.fillRect((_width-1) * max, 0, 1, 1);
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
  var track_rows = $("tr.track_row").filter(":visible");
  var row_count = track_rows.length;
  var notall = (sel_count() < row_count);
  track_rows.each(function() {
    var sel_button = $(this).find(".selectbutton");
    if (notall != sel_button.hasClass('btn-primary')) {
      togglesel(this);
    }
  });
}
function update_selection() {
  selection = Object.create(null);  // reset
  var track_rows = $("tr.track_row").filter(":visible");
  track_rows.each(function() {
    var path = $(this).data('path');
    var index = $(this).data('index');
    var sel_button = $(this).find(".selectbutton");
    if (sel_button.hasClass('btn-primary')) {
      // add to the set
      selection[path] = index;
    }
  });
  update_buttons();
}
function update_buttons() {
  var count = sel_count();
  var track_rows = $("tr.track_row").filter(":visible");
  var row_count = track_rows.length;
  $('#comparebutton').toggleClass('disabled', count != 2);
  $('#comparebutton').toggleClass('btn-primary', count == 2);
  $('#statsbutton').toggleClass('disabled', count == 0);
  $('#statsbutton').toggleClass('btn-primary', count > 0);
  $('#statscsvbutton').toggleClass('disabled', count == 0);
  $('#statscsvbutton').toggleClass('btn-primary', count > 0);
  $('#downloadbutton').toggleClass('disabled', count == 0);
  $('#downloadbutton').toggleClass('btn-primary', count > 0);
  $('#replotselbutton').toggleClass('disabled', count == 0);
  $('#replotselbutton').toggleClass('btn-primary', count > 0);
  $('#archiveselbutton').toggleClass('disabled', count == 0);
  $('#archiveselbutton').toggleClass('btn-primary', count > 0);
  $('._selectallbutton').toggleClass('btn-default', count < row_count);
  $('._selectallbutton').toggleClass('btn-primary', count == row_count);
}

function do_compare() {
  var sels = Object.keys(selection).sort();
  do_post('/compare/', 'p1=' + sels[0] + '&p2=' + sels[1]);
}

function do_stats() {
  var sels = Object.keys(selection).sort();
  do_post('/stats/', 'tracks=' + sels.join('|'));
}

function do_stats_csv() {
  var sels = Object.keys(selection).sort();
  do_post('/stats/', 'csv=true&tracks=' + sels.join('|'));
}

function do_download() {
  var sels = Object.keys(selection).sort();
  do_post('/download/', 'tracks=' + sels.join('|'));
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

function archive_selection() {
  var sels = Object.keys(selection).sort();
  for (var i = 0 ; i < sels.length ; i++) {
    var path = sels[i];
    var index = selection[path];
    do_archive(path, index);
  }
}

function update_ini(iniFile) {
  $.get("/ini/" + iniFile, function(data) {
    lines = data.split('\n');
    real_lines = lines.filter(function(line) {return line[0] != '#';});
    contents = real_lines.join('\n').replace("\n", "");
    $("#inidisplay_name").text(iniFile);
    $("#inidisplay_contents").text(contents);
    $("#inidisplay").show();
  });
}

/*******************************************************************
 * Dynamic form (add/del experiment phases)
 */
function num_phases_enabled() {
    var count = 0;
    $.each($(".phasediv"), function() {
        var enabled = $("#var_enabled", this).val();
        if (enabled == "True") {
            count++;
        }
    });
    return count;
}
function update_phase_ui() {
    var num_enabled = num_phases_enabled();
    $("#phasecount").val(num_enabled);
    $("#btn_addPhase").toggleClass("disabled", (num_enabled >= 10));
    $("#btn_delPhase").toggleClass("disabled", (num_enabled <= 1));
    $.each($(".phasediv"), function() {
        var enabled = $("#var_enabled", this).val();
        $(this).toggleClass('hidden', enabled != "True");
    });
}
function add_phase() {
    var num_enabled = num_phases_enabled();
    if (num_enabled >= 10) return;

    var addphase = $("#phase_" + num_enabled);
    $("#var_enabled", addphase).val("True");
    update_phase_ui();
}
function del_phase() {
    var num_enabled = num_phases_enabled();
    if (num_enabled <= 1) return;

    var delphase = $("#phase_" + (num_enabled-1));
    $("#var_enabled", delphase).val("False");
    update_phase_ui();
}

/*******************************************************************
 * Form caching
 */
function iterate_fields(form, func) {
    var fields = $('*', form).filter(':input');
    $.each(fields, func);
}

function clear_form_data() {
    // clear all fields in localstorage
    iterate_fields($(this).closest('form'), function(i, field) {
        localStorage.removeItem(window.location.pathname + "|" + field.name);
    });
}

function save_form_data() {
    // enumerate and save all fields in localstorage
    iterate_fields(this, function(i, field) {
        var storename = window.location.pathname + "|" + field.name;
        if (field.type == 'radio' || field.type == 'checkbox') {
            if (field.checked) {
                localStorage.setItem(storename, field.value);
            }
        }
        else {
            if (field.value) {
                localStorage.setItem(storename, field.value);
            }
            else {
                localStorage.removeItem(storename);
            }
        }
    });
}

function load_form_data() {
    iterate_fields(this, function(i, field) {
        var storename = window.location.pathname + "|" + field.name;
        var oldval = localStorage.getItem(storename);
        if (!oldval) return;

        if (field.type == 'radio' || field.type == 'checkbox') {
            if (field.value == oldval) { $(field).prop("checked", true); }
        }
        else if (!field.value || field.type == 'select-one') {
            // only update if it's not already filled (except for selects, which are always filled, so...) and we do have something
            $(field).val(oldval);
        }
    });
}

// alert modal
function show_alert(modal_id, title, contents) {
    var modal = $(modal_id);
    modal.find('.modal-title').text(title);
    modal.find('.modal-body').html(contents);
    modal.modal();
}
