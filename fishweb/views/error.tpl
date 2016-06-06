%rebase('base.tpl', title='Error')

<div class="container">
  <h1>Error</h1>

  <div class="row">
    <div class="col-sm-10 col-sm-offset-1">
      <div class="alert alert-danger" role="alert">
        <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
        <span class="sr-only">Error:</span>
        {{errormsg}}
        <pre>{{exception}}</pre>
      </div>
    </div>
  </div>

</div>
