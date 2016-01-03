angular.module('boxesApp', ['ngRoute', 'ngResource'])
.config(['$routeProvider', '$locationProvider',
  function($routeProvider, $locationProvider) {
    $routeProvider
      .when('/', {
        templateUrl: '/static/boxes_view.html',
        controller: 'BoxesCtrl'
      });
}])
.factory('BoxesService', ['$resource',
  function($resource) {
    return $resource('/boxes/', {}, { query: {method: 'GET', params: {}, isArray: false} });
}])
.controller('BoxesCtrl', ['$scope', '$interval', 'BoxesService',
  function($scope, $interval, BoxesService) {
    $scope.boxes = true;  // give ng-show something to go on until boxes is an array
    $interval(function() {
      BoxesService.query({}, function(data) { $scope.boxes = data.toJSON(); });  // toJSON to strip $promise and $resolved so toArray works
    }, 2000);
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
.filter('barwidth', function() {
  return function(lock_data) {
    var start = parseInt(lock_data.starttime)*1000;
    var runtime = parseInt(lock_data.runtime)*1000;
    var startdate = new Date(start);
    var curdate = new Date();
    var millis_gone = curdate.getTime() - startdate.getTime();

    var width = Math.min(100, 100 * millis_gone / runtime);
   
    return width + "%"; 
  };
})
.filter('remaining', function() {
  return function(lock_data, in_out) {
    var start = parseInt(lock_data.starttime)*1000;
    var runtime = parseInt(lock_data.runtime)*1000;
    var startdate = new Date(start);
    var curdate = new Date();
    var millis_remaining = (startdate.getTime() + runtime) - curdate.getTime();
 
    if (in_out == 'in' && millis_remaining < runtime/2
     || in_out == 'out' && millis_remaining > runtime/2) {

        if (millis_remaining < 60*1000) {
            var sec_remaining = Math.round(millis_remaining / 1000);
            var remtext = sec_remaining + " sec remaining";
        }
        else {
            var min_remaining = Math.round(millis_remaining / 1000 / 60);
            var remtext = min_remaining + " min remaining";
        }
        return remtext;
    }
    else {
        return "";
    }
  };
})
.directive('myClearButton', ['$http', function($http) {
  return {
    restrict: 'A',
    link: function(scope, element, attrs, ngModel) {

      function do_clear() {
        var go = confirm("Are you sure?  (The running experiment will be terminated.)");
        if (! go) return;
        $http.post("/clear_experiment/" + attrs.myClearButton, "");
      }

      element.on('click', do_clear);
    }
  };
}])
.directive('mySyncButton', ['$http', function($http) {
  return {
    restrict: 'A',
    link: function(scope, element, attrs, ngModel) {

      function do_sync() {
        var btn = element;
        var txt = btn.find(".btntxt");
        var icon = btn.find(".glyphicon-refresh");

        btn.attr("disabled", true);
        txt.text("Syncing...")
        icon.addClass("rotatey");

        $http.post(
          "/sync/" + attrs.mySyncButton,
          ""
        ).then(
          function success(response) { },
          function error(response) {
            show_alert('#alertModal', 'Sync Failed', response.data);
          }
        ).finally(function() {
          btn.attr("disabled", false);
          txt.text("Sync Data");
          icon.removeClass("rotatey");
        });
          
      };

      element.on('click', do_sync);
    }
  };
}])
;
