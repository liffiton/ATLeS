<!doctype html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Track {{trackrel}}</title>
    <script src="/static/jquery-2.1.4.min.js"></script>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
    <style type="text/css">
        body {
            background: #1f1f1f;  // equiv: 0.12
        }
        img {
            padding: 1em;
        }
    </style>
    <script type="text/javascript">
      $(document).keypress(function(e) {
        if (String.fromCharCode(e.which) == '+') {
          $("img").css('filter', 'brightness(500%)');
          $("img").css('-webkit-filter', 'brightness(500%)');
        }
      });
    </script>
</head>
<body>
<div class="container">
    <h1>Track <a href="/{{trackfile}}">{{trackrel}}</a></h1>
    <div class="text-center">
        %for img in imgs:
            <a href="/{{img}}"><img style='max-width: 100%;' src="/{{img}}"></a>
        %end
    </div>
</div>
</body>
</html>
