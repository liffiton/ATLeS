%import platform
%rebase('base.tpl', title='Track Analyzer/Viewer')

<div class="container">
  <div class="row">
    <div class="my-header col-lg-12 col-md-12 col-sm-12">
      <span class="h1">
        Track Analyzer/Viewer
        %if local:
          on <span class="hostname">{{platform.node()}}</span>
        %end
      </span>
    </div>
  </div>
  <div class="row">
    <div class="col-lg-12 col-md-12 col-sm-12">
      <table class="table table-hover table-vertmid">
        <thead>
          <tr>
            <th>
              <button type="button" class="btn btn-default btn-xs text-muted _selectallbutton" title='Select All'>
                <span class="glyphicon glyphicon-ok"></span>
              </button>
            </th>
            <th>Track file <input type="search" placeholder="filter rows" id="rowfilter"><span id="filterclear">x</span></th>
            <th class="number_cell">Points</th>
            <th class="chart_cell"><acronym title="Acquired/Missing/Lost">A/M/L</acronym></th>
            <th class="chart_cell">Position</th>
            <th class="chart_cell">Velocity</th>
            <th>View</th>
            <th>Actions</th>
          </tr>
        </thead>
        %for index, trackpath, relpath, points, aml, heat, vel, imgs, dbgframes, setupfile in tracks:
        <tr class="undo_row" id="row_{{index}}_undo">
          <td></td>
          <td>{{relpath}}</td>
          <td colspan=5><i>Archived</i></td>
          <td>
            <button type="button" class="btn btn-xs btn-warning" onclick="do_unarchive('{{trackpath}}', {{index}});" title="Unarchive">
              <span class="glyphicon glyphicon-log-in"></span>
              Undo archive
            </button>
          </td>
        </tr>
        <tr class="track_row" id="row_{{index}}" data-path='{{trackpath}}' data-index='{{index}}'>
          <td>
            <button type="button" class="btn btn-default btn-xs text-muted selectbutton" title='Select'>
              <span class="glyphicon glyphicon-ok"></span>
            </button>
          </td>
          <td class="trackfile_cell"><a href="/{{trackpath}}">{{relpath}}</a></td>
          <td class="number_cell">{{points}}</td>
          <td class="chart_cell">
            <canvas class="aml" data-values="{{'|'.join(aml)}}" title="{{' / '.join(aml)}}"></canvas>
          </td>
          <td class="chart_cell">
            %if heat:
            <canvas class="heatmap" data-values="{{heat}}" title="Position heatmap"></canvas>
            %end
          </td>
          <td class="chart_cell">
            %if vel:
            <canvas class="velocity" data-values="{{','.join(vel)}}" title="Avg: {{vel[0]}}  Max: {{vel[1]}}"></canvas>
            %end
          </td>
          <td>
            %if imgs:
            <a href="/view/{{trackpath}}" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-stats"></span> Plots</a>
            %end
            %if dbgframes:
            <a href="/dbgframes/{{trackpath}}" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-camera"></span> Debug</a>
            %end
            %if setupfile:
            <a href="/{{setupfile}}" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-cog"></span> Setup</a>
            %end
          </td>
          <td class="actionbuttons">
            %if points > 0:
            <button type="button" class="btn btn-default btn-xs" onclick="do_post('/analyze/', 'path={{trackpath}}');">
              %if imgs:
              <span class="glyphicon glyphicon-refresh"></span>
              Re-plot
              %else:
              <span class="glyphicon glyphicon-plus"></span>
              Plot
              %end
            </button>
            %end
            <button type="button" class="btn btn-xs btn-danger" onclick="do_archive('{{trackpath}}', {{index}});" title='Archive'>
              <span class="glyphicon glyphicon-log-out"></span>
            </button>
          </td>
        </tr>
        %end
        <tr>
          <td colspan=8>
            <button type="button" class="btn btn-default btn-xs text-muted _selectallbutton" title='Select All'>
              <span class="glyphicon glyphicon-ok"></span> De/Select All
            </button>
          </td>
        </tr>
      </table>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-12 col-md-12 col-sm-12">
      <div class="well">
        <p>
        With selection:
        <button type="button" class="btn btn-default disabled" id="comparebutton" onclick="do_compare();">
          Compare
        </button>
        <button type="button" class="btn btn-default disabled" id="statsbutton" onclick="go_stats();">
          View Statistics
        </button>
        <button type="button" class="btn btn-default disabled" id="statscsvbutton" onclick="go_stats_csv();">
          Download Statistics [.csv]
        </button>
        <button type="button" class="btn btn-default disabled" id="downloadbutton" onclick="do_download();">
          Download Tracks [.zip]
        </button>
        <button type="button" class="btn btn-default disabled" title="Re-plot" id="replotselbutton" onclick="analyze_selection();">
          <span class="glyphicon glyphicon-refresh"></span>
          Re-plot
        </button>
        <button type="button" class="btn btn-default disabled" title="Archive" id="archiveselbutton" onclick="archive_selection();">
          <span class="glyphicon glyphicon-log-out"></span>
          Archive
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
  $("#rowfilter").trigger('input');
  $("._selectallbutton").click(toggle_select_all);
  $("tr.track_row .selectbutton").click(function(e) {
    var row = $(this).closest("tr");
    togglesel(row);
  });
  // create charts/heatmaps
  console.time('aml');
  $("canvas.aml").each(makeAML);
  console.timeEnd('aml');
  console.time('heatmaps');
  $("canvas.heatmap").each(makeHeatMap);
  console.timeEnd('heatmaps');
  console.time('velocities');
  $("canvas.velocity").each(makeVelocityPlot);
  console.timeEnd('velocities');
});
</script>
