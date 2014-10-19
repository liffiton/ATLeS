<!doctype html>
<html>
<head>
    <title>Fishybox Log Analyzer/Viewer</title>
    <script type="text/javascript">
        function post_analyze(path) {
            var form = document.createElement('form');
            form.setAttribute('method', 'post');
            form.setAttribute('action', '/analyze/?path=' + path);
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
<table class="table table-hover" style="max-width: 600px;">
    <thead>
    <tr>
        <th>Log file</th>
        <th># Points</th>
        <th>Plots</th>
        <th>Analyze</th>
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
            <button type="button" class="btn btn-xs" onclick="post_analyze('{{path}}');">
                <span class="glyphicon glyphicon-refresh"></span>
                Re-analyze
            </button>
        %else:
            <button type="button" class="btn btn-xs" onclick="post_analyze('{{path}}');">
                <span class="glyphicon glyphicon-plus"></span>
                Analyze
            </button>
        %end
        </td>
    </tr>
%end
</table>
</div>
</body>
</html>
