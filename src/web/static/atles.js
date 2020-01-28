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

function makeASML() {
    // configuration: number of drawing pixels for bar chart
    var _width = 500;

    var values = $(this).data("values");
    if (!values) return;

    var data = values.split('|');
    var acquired = parseFloat(data[0]);
    var sketchy = parseFloat(data[1]);
    var missing = parseFloat(data[2]);
    var lost = parseFloat(data[3]);
    var a = acquired * _width;
    var b = sketchy * _width;
    var c = missing * _width;
    var d = lost * _width;

    this.width = _width;
    this.height = 1;
    var ctx = this.getContext("2d");

    ctx.fillStyle = "#0d0";
    ctx.fillRect(0,0,a,1);
    ctx.fillStyle = "#cf0";
    ctx.fillRect(a,0,b,1);
    ctx.fillStyle = "#f90";
    ctx.fillRect(a+b,0,c,1);
    ctx.fillStyle = "#d00";
    ctx.fillRect(a+b+c,0,d,1);
}

function putPixel(imgdata, x, y, r, g, b) {
    var i = (x + y*imgdata.width)*4;
    imgdata.data[i] = r;
    imgdata.data[i+1] = g;
    imgdata.data[i+2] = b;
    imgdata.data[i+3] = 255;  // opaque
}

function makeHeatMap() {
    var is_invalid = $(this).hasClass("invalid");

    var rows = $(this).data("values").split('|');

    // get number of buckets from received data
    var _width = rows[0].length/2;  // 2 characters per value
    var _height = rows.length;

    this.width = _width;
    this.height = _height;
    var ctx = this.getContext("2d");
    var imgdata = ctx.createImageData(_width, _height);

    for (var y = 0 ; y < _height ; y++) {
        for (var x = 0 ; x < _width ; x++) {
            var amtstr = rows[y].substr(x*2, 2);
            var amt = parseInt(amtstr, 16)/255;
            amt = Math.sqrt(amt);
            if (is_invalid) {
                var r = Math.floor(240-120*amt);
                var g = Math.floor(240-240*amt);
                var b = Math.floor(240-240*amt);
            } else {
                var r = Math.floor(240-240*amt);
                var g = Math.floor(240-200*amt);
                var b = Math.floor(240-120*amt);
            }
            // _height-1-y because heatmap data is given w/ y=0 = bottom
            putPixel(imgdata, x, _height-1-y, r, g, b);
        }
    }
    ctx.putImageData(imgdata, 0, 0);
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
    ctx.fillStyle = "#f0f0f0";
    ctx.fillRect(0,0,_width, 1);

    ctx.fillStyle = "#0b0";
    ctx.fillRect((_width-1) * avg, 0, 1, 1);

    ctx.fillStyle = "#d00";
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
      sel_button.toggleClass('btn-primary');
    }
  });
  update_selection();
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
  $('.active-if-any').prop('disabled', count == 0);
  $('.active-if-any').toggleClass('btn-primary', count > 0);
  $('.active-if-2plus').prop('disabled', count < 2);
  $('.active-if-2plus').toggleClass('btn-primary', count >= 2);
  $('._selectallbutton').toggleClass('btn-default', count < row_count);
  $('._selectallbutton').toggleClass('btn-primary', count == row_count);
}

function tracksel_go(baseurl, addl_query) {
  var sels = Object.keys(selection).sort();
  var query = 'tracks=' + sels.join('|');
  if (addl_query) {
    query = addl_query + '&' + query;
  }
  window.location = baseurl + "?" + query;
}

function do_archive(trackrel, index) {
  async_post('/archive/', 'trackrel=' + trackrel);
  $("#row_" + index + "_undo").show();
  $("#row_" + index).hide();
}

function do_unarchive(trackrel, index) {
  async_post('/unarchive/', 'trackrel=' + trackrel);
  $("#row_" + index).show();
  $("#row_" + index + "_undo").hide();
}

function analyze_selection() {
  var go = confirm("This operation will run in the background with no feedback while running or when complete (sorry).");
  if (! go) return;
  var sels = Object.keys(selection).sort();
  async_post('/analyze_selection/', 'trackrels=' + sels.join('|'));
}

function archive_selection() {
  var sels = Object.keys(selection).sort();
  for (var i = 0 ; i < sels.length ; i++) {
    var trackrel = sels[i];
    var index = selection[trackrel];
    do_archive(trackrel, index);
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
        var enabled = $(".var_enabled", this).val();
        if (enabled == "True") {
            count++;
        }
    });
    return count;
}
function update_phase_ui() {
    var num_enabled = num_phases_enabled();
    $("#phasecount").val(num_enabled);
    $("#btn_addPhase").prop("disabled", num_enabled >= 10);
    $("#btn_delPhase").prop("disabled", num_enabled <= 1);
    $.each($(".phasediv"), function() {
        var enabled = $(".var_enabled", this).val();
        $(this).toggleClass('hidden', enabled != "True");
    });
}
function add_phase() {
    var num_enabled = num_phases_enabled();
    if (num_enabled >= 10) return;

    var addphase = $("#phase_" + num_enabled);
    $(".var_enabled", addphase).val("True");
    update_phase_ui();
}
function del_phase() {
    var num_enabled = num_phases_enabled();
    if (num_enabled <= 1) return;

    var delphase = $("#phase_" + (num_enabled-1));
    $(".var_enabled", delphase).val("False");
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
        else if (!field.value || field.type == 'select-one' ||
            (field.name.endsWith("-length") && field.value == "0")) {
            // Only update if it's not already filled (except for selects, which are always filled, so...) and we do have something
            // Also special-case length fields, which have been set to 0 by the server but
            // are still fine to override if that's their value.
            $(field).val(oldval);
        }
    });
}

/*******************************************************************
 * Alert modal
 */
function show_alert(modal_id, title, contents) {
    var modal = $(modal_id);
    modal.find('.modal-title').text(title);
    modal.find('.modal-body').html(contents);
    modal.modal();
}
