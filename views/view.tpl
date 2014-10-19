<!doctype html>
<html>
<head>
    <title>Fishybox Log {{logname}}</title>
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css">
</head>
<body>
<div class="container">
    <h1>Fishybox Log {{logname}}</h1>
%for img in imgs:
    <p><img src="/{{img}}"></p>
%end
</div>
</body>
</html>
