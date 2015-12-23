%setdefault('name', '')
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{title}}</title>
<script src="/static/jquery-2.1.4.min.js"></script>
<script src="/static/fishweb.js"></script>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
<link rel="stylesheet" href="/static/fishweb.css">
</head>
<body>
  <nav class="navbar navbar-default navbar-static-top" style="margin-bottom: 0;">
    <div class="container">
      <ul class="nav navbar-nav">
        <li {{!'class="active"' if name == 'boxes' else ''}}>
          <a href="/">Boxes / Experiments
          %if name == 'boxes':
            <span class="sr-only">(current)</span>
          %end
          </a>
        </li>
        <li {{!'class="active"' if name == 'tracks' else ''}}>
          <a href="/tracks/">Tracks
          %if name == 'tracks':
            <span class="sr-only">(current)</span>
          %end
          </a>
        </li>
      </ul>
    </div>
  </nav>
  {{!base}}
</body>
</html>


