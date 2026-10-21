/* Ograje Lozar — interaktivnost (WCAG 2.2, lahka izvedba, brez odvisnosti) */
(function () {
  'use strict';

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Mobilni meni ---------- */
  var burger = document.getElementById('burger');
  var nav = document.getElementById('mainNav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      burger.setAttribute('aria-label', open ? 'Zapri meni' : 'Odpri meni');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        nav.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
        burger.focus();
      }
    });
  }

  /* ---------- Scroll-spy aktivna povezava ---------- */
  var links = Array.prototype.slice.call(document.querySelectorAll('.main-nav a[href^="#"]'));
  var secs = links.map(function (a) { return document.querySelector(a.getAttribute('href')); }).filter(Boolean);
  function spy() {
    var pos = window.scrollY + 140;
    var cur = secs[0];
    for (var i = 0; i < secs.length; i++) { if (secs[i].offsetTop <= pos) cur = secs[i]; }
    links.forEach(function (a) {
      a.classList.toggle('active', cur && a.getAttribute('href') === '#' + cur.id);
    });
  }
  window.addEventListener('scroll', spy, { passive: true });
  spy();

  /* ---------- Reveal animacije ob drsenju ---------- */
  var revs = document.querySelectorAll('.reveal');
  if (!reduce && 'IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    revs.forEach(function (el) { io.observe(el); });
  } else {
    revs.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- Števec statistike v heroju ---------- */
  var counters = document.querySelectorAll('[data-count]');
  function runCount(el) {
    var target = parseInt(el.getAttribute('data-count'), 10);
    var suffix = el.getAttribute('data-suffix') || '';
    if (reduce) { el.textContent = target + suffix; return; }
    var t0 = null;
    function tick(ts) {
      if (!t0) t0 = ts;
      var p = Math.min((ts - t0) / 1400, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  if ('IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (ents) {
      ents.forEach(function (en) { if (en.isIntersecting) { runCount(en.target); cio.unobserve(en.target); } });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { cio.observe(el); });
  } else {
    counters.forEach(runCount);
  }

  /* ---------- Filtri galerije ---------- */
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var figs = Array.prototype.slice.call(document.querySelectorAll('.gal figure[data-cat]'));
  var galCount = document.getElementById('galCount');
  function catsOf(el) { return (el.getAttribute('data-cat') || '').split(/\s+/); }
  function applyFilter(f) {
    var shown = 0;
    figs.forEach(function (fg) {
      var hit = f === 'all' || catsOf(fg).indexOf(f) !== -1;
      fg.classList.toggle('is-hidden', !hit);
      if (hit) shown++;
    });
    if (galCount) galCount.textContent = 'Prikazanih ' + shown + ' od ' + figs.length + ' realizacij.';
  }
  chips.forEach(function (ch) {
    ch.addEventListener('click', function () {
      chips.forEach(function (c) { c.setAttribute('aria-pressed', c === ch ? 'true' : 'false'); });
      applyFilter(ch.getAttribute('data-f'));
    });
  });
  applyFilter('all');

  /* ---------- Lightbox galerija ---------- */
  var lb = document.getElementById('lightbox');
  var lbImg = document.getElementById('lbImg');
  var lbCap = document.getElementById('lbCap');
  var lbCount = document.getElementById('lbCount');
  var galLinks = Array.prototype.slice.call(document.querySelectorAll('.gal a'));
  var idx = 0;
  function visibleLinks() {
    return galLinks.filter(function (a) {
      return !a.closest('figure').classList.contains('is-hidden');
    });
  }
  function show(i) {
    var vis = visibleLinks();
    if (!vis.length) return;
    idx = (i + vis.length) % vis.length;
    var a = vis[idx];
    var img = a.querySelector('img');
    var cap = a.closest('figure').querySelector('figcaption');
    lb._lastA = a;
    lbImg.src = (img && img.currentSrc) || a.href;
    lbImg.alt = (img && img.alt) || '';
    lbCap.textContent = cap ? cap.textContent : '';
    if (lbCount) lbCount.textContent = (idx + 1) + ' / ' + vis.length;
  }
  function openLb(a) {
    var vis = visibleLinks();
    show(vis.indexOf(a));
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    document.getElementById('lbClose').focus();
  }
  function closeLb() {
    lb.hidden = true;
    document.body.style.overflow = '';
    if (lb._lastA) lb._lastA.focus();
  }
  galLinks.forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); openLb(a); });
  });
  if (lb) {
    document.getElementById('lbClose').addEventListener('click', closeLb);
    document.getElementById('lbPrev').addEventListener('click', function () { show(idx - 1); });
    document.getElementById('lbNext').addEventListener('click', function () { show(idx + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) closeLb(); });
    document.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') { closeLb(); return; }
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
      if (e.key === 'Tab') {
        var f = lb.querySelectorAll('button');
        var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
  }

  /* ---------- Obrazec povpraševanja ---------- */
  var EMAIL = 'lesne.storitve@gmail.com';
  var WA = '38641276195';
  var form = document.getElementById('quoteForm');
  if (form) {
    var res = document.getElementById('formResult');
    var msg = document.getElementById('formMsg');
    var acts = document.getElementById('formActions');
    var mailLink = document.getElementById('sendMail');
    var waLink = document.getElementById('sendWa');

    function val(n) {
      var el = form.elements[n];
      return el ? String(el.value).trim() : '';
    }
    function compose() {
      return [
        'Povpraševanje s spletne strani ograje-lozar',
        '',
        'Ime: ' + val('ime'),
        'Telefon: ' + val('tel'),
        'E-pošta: ' + val('mail'),
        'Lokacija objekta: ' + (val('lok') || '—'),
        'Zanima me: ' + val('vrsta'),
        'Okvirna mera: ' + (val('mera') || '—'),
        '',
        'Sporočilo:',
        val('msg') || '—'
      ].join('\n');
    }
    function wire(body) {
      var subject = 'Povpraševanje — ' + val('vrsta') + ' (' + val('ime') + ')';
      mailLink.href = 'mailto:' + EMAIL + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
      waLink.href = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(body);
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var hp = form.elements.podjetje;
      if (hp && hp.value) { hp.value = ''; res.hidden = true; return; }
      if (!form.checkValidity()) { res.hidden = true; form.reportValidity(); return; }

      var body = compose();
      wire(body);
      res.hidden = false;

      var endpoint = (form.getAttribute('data-endpoint') || '').trim();
      if (!endpoint) {
        acts.hidden = false;
        msg.textContent = 'Sporočilo je pripravljeno. Izberi, kje ga odpošlješ — do Igorja pride celotno besedilo, kot si ga vpisal.';
      } else {
        acts.hidden = true;
        msg.textContent = 'Pošiljam …';
        fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({
            ime: val('ime'), tel: val('tel'), mail: val('mail'),
            lok: val('lok'), vrsta: val('vrsta'), mera: val('mera'), msg: val('msg')
          })
        }).then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          msg.textContent = 'Hvala, ' + val('ime') + '. Povpraševanje je bilo poslano — odgovorim na ' + val('tel') + ' ali ' + val('mail') + '.';
          form.querySelectorAll('input,select,textarea,button').forEach(function (el) { el.disabled = true; });
        })['catch'](function () {
          msg.textContent = 'Strežnik za pošiljanje ne odgovarja. Sporočilo je kljub temu pripravljeno — odpošlji ga neposredno.';
          acts.hidden = false;
        });
      }
      res.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    });

    ['ime', 'tel', 'mail', 'lok', 'vrsta', 'mera', 'msg'].forEach(function (n) {
      var el = form.elements[n];
      if (el) el.addEventListener('input', function () { if (!res.hidden) wire(compose()); });
    });
  }

  /* ---------- Header senca + gumb "na vrh" ---------- */
  var head = document.querySelector('.site-head');
  var toTop = document.getElementById('toTop');
  function onScrollUi() {
    var y = window.scrollY;
    if (head) head.classList.toggle('scrolled', y > 8);
    if (toTop) toTop.classList.toggle('show', y > 600);
  }
  window.addEventListener('scroll', onScrollUi, { passive: true });
  onScrollUi();
  if (toTop) {
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
    });
  }

  /* ---------- Leto v nogah ---------- */
  var leto = document.getElementById('leto');
  if (leto) leto.textContent = new Date().getFullYear();
})();
