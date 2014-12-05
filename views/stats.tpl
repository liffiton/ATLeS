<!doctype html>
<html>
<head>
    <title>Fishybox Log Statistics</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.1/css/bootstrap.min.css">
</head>
<body>
    <table class="table text-right">
        <tr>
            <th>Log file</th>
        %for key in keys:
            <th>{{key}}</th>
        %end
        </tr>
        <tbody>
        %for stat in stats:
            <tr>
                <td>{{stat['Log file']}}</td>
            %for key in keys:
                <td>{{stat[key]}}</td>
            %end
            </tr>
        %end
        </tbody>
    </table>
</body>
</html>
