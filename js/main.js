/* Ograje Lozar — interaktivnost (WCAG 2.2, lahka izvedba, brez odvisnosti) */
(function () {
  'use strict';

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
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
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

  /* ---------- Lightbox galerija ---------- */
  var lb = document.getElementById('lightbox');
  var lbImg = document.getElementById('lbImg');
  var lbCap = document.getElementById('lbCap');
  var galLinks = Array.prototype.slice.call(document.querySelectorAll('.gal a'));
  var idx = 0;
  function show(i) {
    idx = (i + galLinks.length) % galLinks.length;
    var a = galLinks[idx];
    lbImg.src = a.href;
    lbImg.alt = a.querySelector('img').alt;
    lbCap.textContent = a.getAttribute('data-caption') || '';
  }
  function openLb(i) {
    show(i);
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    document.getElementById('lbClose').focus();
  }
  function closeLb() {
    lb.hidden = true;
    document.body.style.overflow = '';
    if (galLinks[idx]) galLinks[idx].focus();
  }
  galLinks.forEach(function (a, i) {
    a.addEventListener('click', function (e) { e.preventDefault(); openLb(i); });
  });
  if (lb) {
    document.getElementById('lbClose').addEventListener('click', closeLb);
    document.getElementById('lbPrev').addEventListener('click', function () { show(idx - 1); });
    document.getElementById('lbNext').addEventListener('click', function () { show(idx + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) closeLb(); });
    document.addEventListener('keydown', function (e) {
      if (lb.hidden) return;
      if (e.key === 'Escape') closeLb();
      if (e.key === 'ArrowLeft') show(idx - 1);
      if (e.key === 'ArrowRight') show(idx + 1);
    });
  }

  /* ---------- Obrazec povpraševanja (demo potrditev) ---------- */
  var form = document.getElementById('quoteForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var ok = document.getElementById('formOk');
      ok.hidden = false;
      form.querySelectorAll('input,select,textarea,button').forEach(function (el) { el.disabled = true; });
      ok.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    });
  }

  /* ---------- Leto v nogah ---------- */
  var leto = document.getElementById('leto');
  if (leto) leto.textContent = new Date().getFullYear();
})();
