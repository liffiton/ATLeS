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
    <div class="col-lg-10 col-md-12 col-sm-12">
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
            <th class="svg_cell"><acronym title="Acquired/Missing/Lost">A/M/L</acronym></th>
            <th class="svg_cell">Position heatmap</th>
            <th>View</th>
            <th>Actions</th>
          </tr>
        </thead>
        %for index, path, relpath, points, aml, heat, imgs, dbgframes in tracks:
        <tr class="undo_row" id="row_{{index}}_undo">
          <td></td>
          <td>{{relpath}}</td>
          <td colspan=4><i>Archived</i></td>
          <td>
            <button type="button" class="btn btn-xs btn-warning" onclick="do_unarchive('{{path}}', {{index}});" title="Unarchive">
              <span class="glyphicon glyphicon-log-in"></span>
              Undo archive
            </button>
          </td>
        </tr>
        <tr class="track_row" id="row_{{index}}" data-path='{{path}}' data-index='{{index}}'>
          <td>
            <button type="button" class="btn btn-default btn-xs text-muted selectbutton" title='Select'>
              <span class="glyphicon glyphicon-ok"></span>
            </button>
          </td>
          <td class="trackfile_cell"><a href="/{{path}}">{{relpath}}</a></td>
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
            %if imgs:
            <a href="/view/{{path}}" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-stats"></span> Plots</a>
            %end
            %if dbgframes:
            <a href="/dbgframes/{{path}}" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-camera"></span> Debug</a>
            %end
          </td>
          <td class="actionbuttons">
            %if points > 0:
            <button type="button" class="btn btn-default btn-xs" onclick="do_post('/analyze/', 'path={{path}}');">
              %if imgs:
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
        <tr>
          <td colspan=7>
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
        <button type="button" class="btn btn-default disabled" id="statsbutton" onclick="do_stats();">
          View Statistics
        </button>
        <button type="button" class="btn btn-default disabled" id="statscsvbutton" onclick="do_stats_csv();">
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
  $("._selectallbutton").click(toggle_select_all);
  $("tr.track_row .selectbutton").click(function(e) {
    var row = $(this).closest("tr");
    togglesel(row);
  });
  // create all valid/missing/lost charts by default
  $("svg.aml_chart").each(makeChart);
  // create heatmaps only on mouseover (and only once for each element) to save memory/CPU time
  $("svg.heatmap").one('mouseenter', makeHeatMap);
});
</script>
