<!doctype html>
<html>
<head>
    <title>Fishybox Log Analyzer/Viewer</title>
    <script src="https://code.jquery.com/jquery-2.1.1.min.js"></script>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css">
    <!-- <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min.js"></script> -->
    <script type="text/javascript">
        function do_post(path, query, check) {
            if (check) {
                go = confirm("Are you sure?  (" + check + ")");
                if (! go) return;
            }
            var form = document.createElement('form');
            form.setAttribute('method', 'post');
            form.setAttribute('action', path + "?" + query);
            form.style.display = 'hidden';
            document.body.appendChild(form)
            form.submit();
        }

        // compare_selection holds one selected track for comparison, if any
        var compare_selection = "";
        function set_compare(el, path) {
            e = $(el);
            if (e.hasClass('active')) {
                e.removeClass('active');
                e.removeClass('btn-primary');
                compare_selection = "";
            }
            else {
                e.addClass('active');
                e.addClass('btn-primary');
                if (compare_selection != "") {
                    // if another has been selected, compare the two
                    do_post('/compare/', 'p1=' + compare_selection + '&p2=' + path);
                }
                else {
                    // otherwise, make this the selected one
                    compare_selection = path;
                }
            }
        }
    </script>
</head>
<body>
<div class="container">
<h1>Fishybox Log Analyzer/Viewer</h1>
<table class="table table-hover" style="max-width: 800px;">
    <thead>
    <tr>
        <th>Log file</th>
        <th># Points</th>
        <th>Plots</th>
        <th>Compare</th>
        <th>Actions
            <button type="button" class="btn btn-xs" onclick="do_post('/analyze_all/', null, 'This will take a long time with no feedback while running.');">
                <span class="glyphicon glyphicon-refresh"></span>
                All
            </button>
        </th>
    </tr>
    </thead>
%for path, points, img_count in tracks:
    <tr>
        <td>{{path}}</td>
        <td>{{points}}</td>
        <td>
        %if img_count:
            <a href="/view/{{path}}">View plots</a>
        %end
        </td>
        <td>
        %if img_count:
            <button type="button" class="btn comparebtn btn-xs text-muted" onclick="set_compare(this, '{{path}}');" title='Compare'>
                <span class="glyphicon glyphicon-ok"></span>
            </button>
        %end
        </td>
        <td>
            <button type="button" class="btn btn-xs" onclick="do_post('/analyze/', 'path={{path}}');">
                %if img_count:
                <span class="glyphicon glyphicon-refresh"></span>
                Re-analyze
                %else:
                <span class="glyphicon glyphicon-plus"></span>
                Analyze
                %end
            </button>
            <button type="button" class="btn btn-xs btn-danger" onclick="do_post('/archive/', 'path={{path}}', 'This is difficult to undo.');" title='Archive'>
                <span class="glyphicon glyphicon-log-out"></span>
            </button>
        </td>
    </tr>
%end
</table>
</div>
</body>
</html>
