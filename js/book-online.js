/* Book online on hub, town, and service pages.
   Opens SCWS's public Jobber request form in a new tab.
   Estimate, call, and text links stay on /contact.html and the shop numbers.
   Voice number stays (760) 440-8520; call-tracking.js swaps it. */
(function () {
  var BOOK_URL = 'https://clienthub.getjobber.com/hubs/7c569177-85d0-4bac-9c7f-e2afe6652ee1/public/requests/1604593/new';

  function point(link) {
    link.href = BOOK_URL;
    link.target = '_blank';
    link.rel = 'noopener';
  }

  function place() {
    if (!document.body) return;
    var path = location.pathname || '';
    if (path.indexOf('/services/') === -1) return;
    var existing = document.querySelectorAll('a.scws-book-online');
    if (existing.length) {
      for (var i = 0; i < existing.length; i++) point(existing[i]);
      return;
    }
    var link = document.createElement('a');
    link.id = 'scws-book-online';
    link.className = 'scws-book-online';
    link.textContent = 'Book online';
    point(link);
    var hero = document.querySelector('main .hero') || document.querySelector('.hero');
    if (!hero) return;
    var call = hero.querySelector('a[href^="tel:"]');
    if (call && call.parentNode) call.parentNode.insertBefore(link, call.nextSibling);
    else hero.appendChild(link);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', place);
  else place();
})();
