%setdefault('name', '')
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{title}}</title>
<script src="/static/jquery-2.1.4.min.js"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-0mSbJDEHialfmuBBQP6A4Qrprq5OVfW37PRR3j5ELqxss1yVqOtnepnHVP9aJ7xS" crossorigin="anonymous"></script>
<script src="/static/fishweb.js"></script>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css" integrity="sha384-1q8mTJOASx8j1Au+a5WDVnPi2lkFfwwEAa8hDDdjZlpLegxhjVME1fgjWPGmkzs7" crossorigin="anonymous">
<link rel="stylesheet" href="/static/fishweb.css">
</head>
<body>
  <!-- Navbar -->
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

  <!-- Modal for alerts -->
  <div class="modal fade" id="alertModal" tabindex="-1" role="dialog" aria-labelledby="alertModalLabel">
    <div class="modal-dialog" role="document">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
          <h4 class="modal-title" id="alertModalLabel">Alert</h4>
        </div>
        <div class="modal-body">
          <pre>
          </pre>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  </div>

  <!-- Content -->
  {{!base}}

</body>
</html>


