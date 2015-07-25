<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fishybox Log {{logname}}</title>
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
    <style type="text/css">
        body {
            background: #1f1f1f;  // equiv: 0.12
        }
        img {
            padding: 1em;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Fishybox Log <a href="/{{logname}}">{{logname}}</a></h1>
    <div class="text-center">
        %for img in imgs:
            <a href="/{{img}}"><img style='max-width: 100%;' src="/{{img}}"></a>
        %end
    </div>
</div>
</body>
</html>
