angular.module('BoxesApp', ['ngResource'])
.factory('BoxesService', ['$resource',
  function($resource) {
    return $resource('/boxes/', {}, { query: {method: 'GET', params: {}, isArray: false} });
}])
.controller('BoxesCtrl', ['$scope', '$interval', 'toArrayFilter', 'BoxesService',
  function($scope, $interval, toArrayFilter, BoxesService) {
    $scope.boxes = null;  // give ng-show something to go on until boxes is an array
    function update() {
      BoxesService.query(
              {},
              function(data) { $scope.boxes = toArrayFilter(data.toJSON()); },  // toJSON to strip $promise and $resolved so toArray works
              function(data) { $scope.boxes = "error"; }  // error-handler; signal page via "error" string
              );
    };
    $interval(update, 2000);
    update(); // call once to start
}])
.filter('toArray', function () {
  // based on https://github.com/petebacondarwin/angular-toArrayFilter/
  return function (obj) {
    if (!angular.isObject(obj)) return obj;
    return Object.keys(obj).map(function(key) {
      return obj[key];
    });
  };
})
.filter('since', function() {
  return function(lock_data) {
    var starttime = new Date(parseInt(lock_data.starttime)*1000);
    return starttime.toLocaleTimeString();
  };
})
.filter('barwidth', function() {
  return function(lock_data) {
    var starttime = parseInt(lock_data.starttime);
    var runtime = parseInt(lock_data.runtime);
    var curtime = parseInt(lock_data.curtime);
    var elapsed = curtime - starttime;

    var width = Math.min(100, 100 * elapsed / runtime);
   
    return width;
  };
})
.filter('remaining', function() {
  return function(lock_data, in_out) {
    var starttime = parseInt(lock_data.starttime);
    var runtime = parseInt(lock_data.runtime);
    var curtime = parseInt(lock_data.curtime);

    var sec_remaining = starttime+runtime - curtime;
 
    if (in_out == 'in' && sec_remaining < runtime/2
     || in_out == 'out' && sec_remaining > runtime/2) {

        if (sec_remaining < 60) {
            var remtext = sec_remaining + " sec remaining";
        }
        else {
            var min_remaining = Math.round(sec_remaining / 60);
            var remtext = min_remaining + " min remaining";
        }
        return remtext;
    }
    else {
        return "";
    }
  };
})
.directive('sparkline', function() {
  return {
    restrict: 'A',
    scope: {
        data: '=ngModel'
    },
    link: function(scope, element, attrs) {
      var data = scope.data;
      var len = data.length;

      var lineWidth = 8;

      var canvas = element[0];
      canvas.width = 400;
      canvas.height = 100;
      var ctx = element[0].getContext('2d');

      /*
      // shade background
      ctx.fillStyle = "#eeeeee";
      ctx.rect(0,0,element[0].width,element[0].height);
      ctx.fill();
      */

      // parameters for data region
      var w = element[0].width;
      var h = element[0].height - 2*lineWidth;
      var ptspacing = w/(len-1);

      // scale a data value in a y-coordinate for the canvas
      // based on requested line type
      var type = attrs.sparklineType;
      if (type == null) {
        type = "yMinMax";
      }
      var getY = function(dataval) {
        var min = Math.min.apply(null, data);
        var max = Math.max.apply(null, data);
        // dataY is scaled from 0 to 1 (0=bottom, 1=top)
        if (type == "yMinMax") {
          var dataY = (dataval-min) / (max-min);
        }
        if (type == "yPercent") {
          var dataY = dataval;
        }
        // canvasY is actual pixel coordinates
        // aiming to draw all in a region w/ a lineWidth buffer
        // on top and bottom
        var canvasY = (1-dataY)*h + lineWidth;
        return canvasY;
      }

      // draw sparkline
      var color = "#0066cc";
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      ctx.beginPath();
      ctx.moveTo(0, getY(data[0]));
      for (var i = 1 ; i < len ; i++) {
        ctx.lineTo(i*ptspacing, getY(data[i]));
      }
      ctx.stroke();
      /*
      // draw circles marking each datapoint
      ctx.fillStyle = color;
      for (var i = 0 ; i < len ; i++) {
        ctx.beginPath();
        ctx.arc(i*ptspacing, getY(data[i]), lineWidth*1.5, 2*Math.PI, false);
        ctx.fill();
      }
      */
    }
  };
})
.directive('myClearButton', ['$http', function($http) {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {

      function do_clear() {
        var go = confirm("Are you sure?  (The running experiment will be terminated.)");
        if (! go) return;
        $http.post("/clear_experiment/" + attrs.myClearButton, "");
      }

      element.on('click', do_clear);
    }
  };
}])
;
