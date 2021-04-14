//https://gist.github.com/jed/982883
function uuid(a){return a?(a^Math.random()*16>>a/4).toString(16):([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g,uuid)}

function getCookieValue(a) {
  var b = document.cookie.match('(^|[^;]+)\\s*' + a + '\\s*=\\s*([^;]+)');
  return b ? b.pop() : '';
}

function setCookieValue(name, value) {
  document.cookie = name+'='+value+'; SameSite=None; Secure';
}

var Pipeless = {
  like: function(user_id, imdb) {
    $.post(`/like/${user_id}/${imdb}`, function(data, status) {
      if (status == 'success') {
        $("#like").attr("disabled",true);
        $("#dislike").attr("disabled",false);
      }
   });
  },

  dislike: function(user_id, imdb) {
    $.post(`/dislike/${user_id}/${imdb}`, function(data, status) {
      if (status == 'success') {
        $("#dislike").attr("disabled",true);
        $("#like").attr("disabled",false);
      }
   });
  }
}

$(document).ready(function() {
  var user_id = getCookieValue('user_id');
  if (user_id == '') {
    setCookieValue('user_id', uuid());
  }
});

function resetUserId() {
  setCookieValue('user_id', uuid());
  window.location=window.location;
}