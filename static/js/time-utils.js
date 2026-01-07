(function () {
  function formatFriendlyTime(value, now) {
    if (!value) {
      return '';
    }
    var date = value instanceof Date ? value : new Date(value);
    if (isNaN(date.getTime())) {
      return '';
    }
    var nowDate = now instanceof Date ? now : new Date();
    var deltaSeconds = Math.floor((nowDate.getTime() - date.getTime()) / 1000);
    var future = deltaSeconds < 0;
    var seconds = Math.abs(deltaSeconds);
    var suffix = future ? 'from now' : 'ago';

    if (seconds < 45) {
      return future ? 'in a moment' : 'just now';
    }
    if (seconds < 90) {
      return '1 minute ' + suffix;
    }

    var minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
      return minutes + ' minutes ' + suffix;
    }

    var hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return hours + ' hour' + (hours === 1 ? '' : 's') + ' ' + suffix;
    }

    var days = Math.floor(hours / 24);
    if (days === 1) {
      return future ? 'tomorrow' : 'yesterday';
    }
    if (days < 7) {
      return days + ' days ' + suffix;
    }

    var weeks = Math.floor(days / 7);
    if (weeks < 5) {
      return weeks + ' week' + (weeks === 1 ? '' : 's') + ' ' + suffix;
    }

    var sameYear = date.getFullYear() === nowDate.getFullYear();
    var dateOptions = { month: 'short', day: '2-digit' };
    if (!sameYear) {
      dateOptions.year = 'numeric';
    }
    var datePart = date.toLocaleDateString(undefined, dateOptions);
    var timePart = date.toLocaleTimeString(undefined, {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });

    if (sameYear) {
      return datePart + ' at ' + timePart;
    }
    return datePart + ' ' + timePart;
  }

  window.formatFriendlyTime = formatFriendlyTime;
})();
