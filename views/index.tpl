<!doctype html>
<html>
<head>
    <title>Fishybox Log Analyzer/Viewer</title>
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
    </script>
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css">
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
