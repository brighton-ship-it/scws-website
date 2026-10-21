/* SCWS job map ("check-in" pins). Town-level pins only: no names, no addresses.
   Usage: <div class="scws-job-map" data-center="33.05,-116.88" data-radius-km="45" data-zoom="10"></div>
   Data: /recent-work/job-map.json (built by scripts/build_job_map.py from projects.json). */
(function () {
  var LCSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
  var LJS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
  function load(cb) {
    if (window.L) return cb();
    var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = LCSS; document.head.appendChild(l);
    var s = document.createElement('script'); s.src = LJS; s.onload = cb; document.head.appendChild(s);
  }
  function km(a, b, c, d) {
    var R = 6371, r = Math.PI / 180, x = (c - a) * r, y = (d - b) * r;
    var h = Math.sin(x / 2) * Math.sin(x / 2) + Math.cos(a * r) * Math.cos(c * r) * Math.sin(y / 2) * Math.sin(y / 2);
    return 2 * R * Math.asin(Math.sqrt(h));
  }
  function esc(t) { return String(t || '').replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function init(el, data) {
    var c = (el.getAttribute('data-center') || '33.3,-116.9').split(',').map(Number);
    var rad = Number(el.getAttribute('data-radius-km') || 0);
    var zoom = Number(el.getAttribute('data-zoom') || 9);
    var pins = data.pins.filter(function (p) { return !rad || km(c[0], c[1], p.lat, p.lng) <= rad; });
    var map = L.map(el, { scrollWheelZoom: false }).setView(c, zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 15, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
    var colors = {
      'Pump Service': '#c53030',
      'Pressure Tanks': '#2b6cb0',
      'Well Drilling': '#2f855a',
      'Water Quality': '#6b46c1',
      'Maintenance': '#c05621'
    };
    pins.forEach(function (p) {
      var img = p.photo ? '<img src="/images/recent-work/' + esc(p.photo) + '" alt="' + esc(p.title + ' in ' + p.town) + '" width="240" height="150" loading="lazy" decoding="async" style="width:240px;height:150px;object-fit:cover;border-radius:6px;display:block;margin-bottom:6px">' : '';
      var town = p.serviceHref ? '<a href="' + esc(p.serviceHref) + '">' + esc(p.town) + ' well service</a>' : esc(p.town);
      var html = img + '<strong>' + esc(p.title) + '</strong><br>' + esc(p.category || '') + '<br>' + town + ' · ' + esc(p.dateLabel) + '<br><a href="/recent-work/' + esc(p.slug) + '.html">See the job →</a><br><a href="tel:+17604630493">Call (760) 463-0493</a>';
      L.circleMarker([p.lat, p.lng], {
        radius: 7,
        color: '#fff',
        weight: 1.5,
        fillColor: colors[p.category] || '#c53030',
        fillOpacity: 0.92
      }).bindPopup(html, { maxWidth: 260 }).addTo(map);
    });
    var cnt = el.parentNode.querySelector('.scws-job-map-count');
    if (cnt) cnt.textContent = pins.length + ' completed jobs on the map';
  }
  function run() {
    var els = document.querySelectorAll('.scws-job-map');
    if (!els.length) return;
    fetch('/recent-work/job-map.json').then(function (r) { return r.json(); }).then(function (data) {
      load(function () { for (var i = 0; i < els.length; i++) init(els[i], data); });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
