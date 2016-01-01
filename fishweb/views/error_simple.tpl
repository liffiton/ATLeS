%from bottle import DEBUG
<h3>Error {{e.status}}:</h3>
<pre>{{e.body}}</pre>
%if DEBUG and e.exception:
  <h4>Exception:</h4>
  <pre>{{repr(e.exception)}}</pre>
%end
%if DEBUG and e.traceback:
  <h4>Traceback:</h4>
  <pre>{{e.traceback}}</pre>
%end
