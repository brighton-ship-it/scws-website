/* Book online on hub, town, and service pages.
   scws-website and scws-jobs have no public Jobber work-request URL
   (client hub links there are invoice pay links, not a booking form).
   This button opens the existing estimate form at /contact.html.
   Voice number stays (760) 440-8520; call-tracking.js swaps it. */
(function () {
  var BOOK_URL = '/contact.html';

  function place() {
    if (!document.body || document.getElementById('scws-book-online')) return;
    var path = location.pathname || '';
    if (path.indexOf('/services/') === -1) return;
    var link = document.createElement('a');
    link.id = 'scws-book-online';
    link.className = 'scws-book-online';
    link.href = BOOK_URL;
    link.textContent = 'Book online';
    var hero = document.querySelector('main .hero') || document.querySelector('.hero');
    if (!hero) return;
    var call = hero.querySelector('a[href^="tel:"]');
    if (call && call.parentNode) call.parentNode.insertBefore(link, call.nextSibling);
    else hero.appendChild(link);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', place);
  else place();
})();
