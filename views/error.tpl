% rebase('base.tpl', title='Error')

<div class="container">
  <h1>Fishybox: Error</h1>

  <div class="row">
    <div class="col-lg-6 col-md-8 col-sm-10">
      <div class="alert alert-danger" role="alert">
        <span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>
        <span class="sr-only">Error:</span>
        {{errormsg}}
      </div>
    </div>
  </div>

</div>
