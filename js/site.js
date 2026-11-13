/* Felicia Chuma: site behaviour.
   Covers navigation, reveal-on-scroll, back-to-top, reading progress,
   the photo gallery + lightbox, and the contact form.
   Every feature degrades gracefully: the page is fully readable without JS. */
(function () {
  var d = document, root = d.documentElement;

  /* -------------------------------------------------- mobile navigation */
  var menuBtn = d.getElementById('menu-btn'), nav = d.getElementById('site-nav');
  if (menuBtn && nav) {
    var setOpen = function (open) {
      nav.classList.toggle('open', open);
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    };
    menuBtn.addEventListener('click', function () { setOpen(!nav.classList.contains('open')); });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) { setOpen(false); menuBtn.focus(); }
    });
    nav.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });
  }

  /* -------------------------------------------------- reveal on scroll */
  var revealItems = [].slice.call(d.querySelectorAll('.reveal'));
  if (revealItems.length) {
    if (!('IntersectionObserver' in window)) {
      revealItems.forEach(function (el) { el.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
      revealItems.forEach(function (el) { io.observe(el); });
      /* Safety net: never leave content hidden. */
      setTimeout(function () { revealItems.forEach(function (el) { el.classList.add('in'); }); }, 5000);
    }
  }

  /* -------------------------------------------------- back to top + progress */
  var toTop = d.getElementById('to-top'), bar = d.getElementById('progress-bar');
  var ticking = false;
  function onScroll() {
    var y = window.scrollY || root.scrollTop;
    if (toTop) toTop.classList.toggle('show', y > 700);
    if (bar) {
      var art = d.getElementById('article-body');
      if (art) {
        var r = art.getBoundingClientRect(), total = r.height - window.innerHeight * 0.6;
        var p = Math.min(1, Math.max(0, (-r.top + window.innerHeight * 0.2) / Math.max(total, 1)));
        bar.style.width = (p * 100).toFixed(1) + '%';
      } else {
        var docH = d.documentElement.scrollHeight - window.innerHeight;
        bar.style.width = (docH > 0 ? Math.min(1, y / docH) * 100 : 0).toFixed(1) + '%';
      }
    }
    ticking = false;
  }
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();
  if (toTop) toTop.addEventListener('click', function () {
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
  });

  /* -------------------------------------------------- photo gallery + lightbox */
  (function () {
    var figs = [].slice.call(d.querySelectorAll('#gallery figure'));
    if (!figs.length) return;
    var chips = [].slice.call(d.querySelectorAll('[data-collection-filter]'));
    var empty = d.getElementById('gallery-empty');
    var dlg = d.getElementById('lightbox');
    var current = -1;

    function visible() { return figs.filter(function (f) { return !f.hidden; }); }
    function filter(val) {
      var n = 0;
      figs.forEach(function (f) {
        var ok = !val || f.getAttribute('data-collection') === val;
        f.hidden = !ok;
        if (ok) n++;
      });
      chips.forEach(function (c) { c.setAttribute('aria-pressed', c.getAttribute('data-collection-filter') === val ? 'true' : 'false'); });
      if (empty) empty.hidden = n !== 0;
    }
    chips.forEach(function (c) { c.addEventListener('click', function () { filter(c.getAttribute('data-collection-filter')); }); });

    if (!dlg || typeof dlg.showModal !== 'function') return;
    var img = dlg.querySelector('img'), cap = dlg.querySelector('figcaption');
    function show(i) {
      var v = visible(); if (!v.length) return;
      current = (i + v.length) % v.length;
      var f = v[current], b = f.querySelector('button');
      img.src = b.getAttribute('data-large');
      img.alt = b.getAttribute('data-alt');
      cap.textContent = f.querySelector('figcaption').textContent;
    }
    figs.forEach(function (f) {
      f.querySelector('button').addEventListener('click', function () {
        show(visible().indexOf(f)); dlg.showModal();
      });
    });
    dlg.querySelector('.close').addEventListener('click', function () { dlg.close(); });
    dlg.querySelector('[data-prev]').addEventListener('click', function () { show(current - 1); });
    dlg.querySelector('[data-next]').addEventListener('click', function () { show(current + 1); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') show(current + 1);
      if (e.key === 'ArrowLeft') show(current - 1);
    });
  })();

  /* -------------------------------------------------- contact form */
  (function () {
    var form = d.getElementById('contact-form');
    if (!form) return;
    var status = d.getElementById('form-status');
    var started = Date.now();
    var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

    function field(name) { return form.elements[name]; }
    function mark(name, ok) {
      var el = field(name); if (!el) return;
      var wrap = el.closest('.field'); wrap.classList.toggle('invalid', !ok);
      el.setAttribute('aria-invalid', ok ? 'false' : 'true');
    }
    function validate() {
      var ok = true, first = null;
      var rules = {
        name: function (v) { return v.trim().length >= 2; },
        email: function (v) { return emailRe.test(v.trim()); },
        subject: function (v) { return v.trim().length >= 3; },
        message: function (v) { return v.trim().length >= 10; }
      };
      Object.keys(rules).forEach(function (k) {
        var good = rules[k](field(k).value); mark(k, good);
        if (!good) { ok = false; if (!first) first = field(k); }
      });
      if (first) first.focus();
      return ok;
    }
    function say(kind, msg) { status.className = 'form-status ' + kind; status.textContent = msg; }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      status.className = 'form-status'; status.textContent = '';
      if (field('website').value) { say('ok', 'Thank you. Your message has been sent.'); return; } /* bot: pretend success */
      if (!validate()) { say('bad', 'Please fix the highlighted fields and try again.'); return; }
      if (Date.now() - started < 2500) { say('bad', 'That was very quick. Please check your message and send it again.'); return; }
      var data = {
        name: field('name').value.trim(), email: field('email').value.trim(),
        organisation: field('organisation').value.trim(), subject: field('subject').value.trim(),
        message: field('message').value.trim()
      };
      var endpoint = form.getAttribute('data-endpoint'), mailto = form.getAttribute('data-mailto');
      var btn = form.querySelector('button[type=submit]');
      if (endpoint) {
        btn.disabled = true; say('ok', 'Sending\u2026');
        fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(data) })
          .then(function (r) {
            if (!r.ok) throw new Error('bad status');
            form.reset(); say('ok', 'Thank you, ' + data.name.split(' ')[0] + '. Your message has been sent and I will reply soon.');
          })
          .catch(function () { say('bad', 'Sorry, the message could not be sent. Please try again, or reach out on LinkedIn.'); })
          .then(function () { btn.disabled = false; });
      } else if (mailto) {
        var body = data.message + '\n\nFrom: ' + data.name + (data.organisation ? ' (' + data.organisation + ')' : '') + '\n' + data.email;
        window.location.href = 'mailto:' + mailto + '?subject=' + encodeURIComponent(data.subject) + '&body=' + encodeURIComponent(body);
        say('ok', 'Your email app should open with the message ready to send. If it does not, please write to ' + mailto + '.');
      } else {
        say('bad', 'Direct sending is not switched on yet. Please connect with me on LinkedIn instead.');
      }
    });
    [].slice.call(form.querySelectorAll('input,textarea')).forEach(function (el) {
      el.addEventListener('input', function () {
        var w = el.closest('.field');
        if (w && w.classList.contains('invalid')) { w.classList.remove('invalid'); el.setAttribute('aria-invalid', 'false'); }
      });
    });
  })();
})();
