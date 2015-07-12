<!doctype html>
<html>
<head>
    <title>Fishybox Log Analyzer/Viewer</title>
    <script src="https://code.jquery.com/jquery-2.1.3.min.js"></script>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
    <style>
        tr.undo_row {
            display: none;  /* default, will be overridden to display */
            color: #999999;
            background: #eeeeee;
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

        // keep track of selected tracks
        var selection = Object.create(null);  // an empty object to be used as a set
        function toggle_select(el, path) {
            var e = $(el);
            e.toggleClass('btn-primary');
            if (e.hasClass('btn-primary')) {
                // add to the set
                selection[e.data('path')] = true;
            } else {
                // remove from the set
                delete selection[e.data('path')];
            }

            var count = Object.keys(selection).length;
            $('#comparebutton').toggleClass('disabled', count != 2);
            $('#comparebutton').toggleClass('btn-primary', count == 2);
            $('#statsbutton').toggleClass('disabled', count == 0);
            $('#statsbutton').toggleClass('btn-primary', count > 0);
            $('#statscsvbutton').toggleClass('disabled', count == 0);
            $('#statscsvbutton').toggleClass('btn-primary', count > 0);
        }
        function toggle_select_all() {
            var count = Object.keys(selection).length;
            var els = $('.selectbutton');
            els.each(function(i, el) {
                if ((count < els.length) != ($(el).hasClass('btn-primary'))) {
                    $(el).click();
                }
            });
            count = Object.keys(selection).length;
            $('#selectallbutton').toggleClass('btn-primary', count == els.length);
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
<h1>Fishybox Log Analyzer/Viewer</h1>
<div class="row">
    <div class="col-md-8">
        <table class="table table-hover" style="max-width: 700px;">
            <thead>
            <tr>
                <th>
                    <button type="button" class="btn btn-default btn-xs text-muted" id="selectallbutton" onclick="toggle_select_all();" title='Select All'>
                        <span class="glyphicon glyphicon-ok"></span>
                    </button>
                </th>
                <th>Log file</th>
                <th># Points</th>
                <th>Plots</th>
                <th>Actions</th>
            </tr>
            </thead>
        %for index, path, points, img_count in tracks:
            <tr class="undo_row" id="row_{{index}}_undo">
                <td></td>
                <td>{{path}}</td>
                <td><i>Archived</i></td>
                <td></td>
                <td>
                    <button type="button" class="btn btn-xs btn-warning" onclick="do_unarchive('{{path}}', {{index}});" title="Unarchive">
                        <span class="glyphicon glyphicon-log-in"></span>
                        Undo archive
                    </button>
                </td>
            </tr>
            <tr id="row_{{index}}">
                <td>
                %if img_count:
                    <button type="button" class="btn btn-default btn-xs text-muted selectbutton" data-path='{{path}}' onclick="toggle_select(this);" title='Select'>
                        <span class="glyphicon glyphicon-ok"></span>
                    </button>
                %end
                </td>
                <td><a href="/{{path}}">{{path}}</a></td>
                <td>{{points}}</td>
                <td>
                %if img_count:
                    <a href="/view/{{path}}">View</a>
                %end
                </td>
                <td>
                    %if points > 0:
                    <button type="button" class="btn btn-default btn-xs" onclick="do_post('/analyze/', 'path={{path}}');">
                        %if img_count:
                        <span class="glyphicon glyphicon-refresh"></span>
                        Re-analyze
                        %else:
                        <span class="glyphicon glyphicon-plus"></span>
                        Analyze
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
