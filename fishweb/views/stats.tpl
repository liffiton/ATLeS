<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fishybox Log Statistics</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
</head>
<body>
    <table class="table text-right">
        <tr>
        %for key in keys:
            <th>{{key}}</th>
        %end
        </tr>
        <tbody>
        %for stat in stats:
            <tr>
            %for key in keys:
                <td>{{stat[key]}}</td>
            %end
            </tr>
        %end
        </tbody>
    </table>
</body>
</html>
