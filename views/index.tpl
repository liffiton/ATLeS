% rebase('base.tpl', title='Log Analyzer/Viewer')

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
        Fishybox Log Analyzer/Viewer: <span class="hostname">{{hostname}}</span>
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
