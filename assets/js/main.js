/* True Faith Church — site interactions */
(function () {
  'use strict';

  var header = document.querySelector('header.main-header');
  var sticky = document.querySelector('.header-sticky');
  var toggle = document.querySelector('.navbar-toggle');
  var menu = document.querySelector('.main-menu');
  var submenus = Array.prototype.slice.call(document.querySelectorAll('.main-menu li.submenu'));
  var mobileQuery = window.matchMedia('(max-width: 1200px)');

  /* ---------- Dropdowns ---------- */
  function closeSubmenu(li) {
    li.classList.remove('open');
    var btn = li.querySelector('.submenu-toggle');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }
  function openSubmenu(li) {
    li.classList.add('open');
    var btn = li.querySelector('.submenu-toggle');
    if (btn) btn.setAttribute('aria-expanded', 'true');
  }
  function closeAll(except) {
    submenus.forEach(function (li) { if (li !== except) closeSubmenu(li); });
  }

  submenus.forEach(function (li) {
    var btn = li.querySelector('.submenu-toggle');
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (li.classList.contains('open')) {
        closeSubmenu(li);
      } else {
        closeAll(li);
        openSubmenu(li);
      }
    });
    // Desktop: hover opens (CSS) — keep ARIA in sync and drop click-opened state on leave
    li.addEventListener('mouseenter', function () {
      if (!mobileQuery.matches) btn.setAttribute('aria-expanded', 'true');
    });
    li.addEventListener('mouseleave', function () {
      if (!mobileQuery.matches) closeSubmenu(li);
    });
    // Keyboard: arrow down opens and focuses first item
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        closeAll(li);
        openSubmenu(li);
        var first = li.querySelector('ul a');
        if (first) first.focus();
      }
    });
    // Close when focus leaves the submenu
    li.addEventListener('focusout', function (e) {
      if (!mobileQuery.matches && !li.contains(e.relatedTarget)) closeSubmenu(li);
    });
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.main-menu li.submenu')) {
      if (!mobileQuery.matches) closeAll();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var openLi = document.querySelector('.main-menu li.submenu.open');
    if (openLi) {
      closeSubmenu(openLi);
      openLi.querySelector('.submenu-toggle').focus();
    } else if (header.classList.contains('menu-open')) {
      setMobileMenu(false);
      toggle.focus();
    }
  });

  /* ---------- Mobile menu ---------- */
  function setMobileMenu(open) {
    header.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    if (!open) closeAll();
  }
  if (toggle) {
    toggle.addEventListener('click', function () {
      setMobileMenu(!header.classList.contains('menu-open'));
    });
  }
  // Leaving mobile width resets the mobile state
  mobileQuery.addEventListener('change', function () { setMobileMenu(false); });
  // Tapping a real page link inside the mobile menu closes it
  menu.querySelectorAll('a[href]').forEach(function (a) {
    a.addEventListener('click', function () { if (mobileQuery.matches) setMobileMenu(false); });
  });

  /* ---------- Current page highlighting ---------- */
  var here = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  // Pages that aren't in the menu (e.g. a region page) name the menu item to highlight
  if (document.body.getAttribute('data-nav-parent')) here = document.body.getAttribute('data-nav-parent').toLowerCase();
  menu.querySelectorAll('a[href]').forEach(function (a) {
    var target = a.getAttribute('href').split('#')[0].toLowerCase();
    if (target === here) {
      a.setAttribute('aria-current', 'page');
      var li = a.parentElement;
      li.classList.add('current');
      var parent = li.parentElement.closest('li.submenu');
      if (parent) parent.classList.add('current');
    }
  });

  /* ---------- Sticky header (hide on scroll down, show on scroll up) ---------- */
  var lastY = window.scrollY;
  function onScroll() {
    var y = window.scrollY;
    var threshold = 300;
    if (y > threshold) {
      sticky.classList.add('active');
      if (y > lastY && !header.classList.contains('menu-open') && !document.querySelector('.main-menu li.open')) {
        sticky.classList.add('hide');
      } else {
        sticky.classList.remove('hide');
      }
    } else {
      sticky.classList.remove('active', 'hide');
    }
    lastY = y;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Reveal on scroll ---------- */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- Counters ---------- */
  var counters = document.querySelectorAll('[data-count]');
  function runCounter(el) {
    var end = parseInt(el.getAttribute('data-count'), 10);
    var suffix = el.getAttribute('data-suffix') || '';
    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / 1600, 1);
      el.textContent = Math.floor(end * (1 - Math.pow(1 - p, 3))) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  if ('IntersectionObserver' in window) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { runCounter(en.target); co.unobserve(en.target); }
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { co.observe(el); });
  }

  /* ---------- Interactive worship columns ---------- */
  var iItems = document.querySelectorAll('.interactive-item');
  var iBgs = document.querySelectorAll('.interactive-bg');
  iItems.forEach(function (item, i) {
    function activate() {
      iItems.forEach(function (x) { x.classList.remove('active'); });
      iBgs.forEach(function (x) { x.classList.remove('active'); });
      item.classList.add('active');
      if (iBgs[i]) iBgs[i].classList.add('active');
    }
    item.addEventListener('mouseenter', activate);
    item.addEventListener('click', activate);
    item.addEventListener('focusin', activate);
  });

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll('.faq-item').forEach(function (item) {
    var q = item.querySelector('.faq-q');
    var a = item.querySelector('.faq-a');
    if (item.classList.contains('open')) a.style.maxHeight = a.scrollHeight + 'px';
    q.addEventListener('click', function () {
      var isOpen = item.classList.contains('open');
      document.querySelectorAll('.faq-item.open').forEach(function (o) {
        o.classList.remove('open');
        o.querySelector('.faq-a').style.maxHeight = null;
        o.querySelector('.faq-q').setAttribute('aria-expanded', 'false');
      });
      if (!isOpen) {
        item.classList.add('open');
        a.style.maxHeight = a.scrollHeight + 'px';
        q.setAttribute('aria-expanded', 'true');
      }
    });
  });

  /* ---------- Donation amounts ---------- */
  var amountInput = document.getElementById('donate-amount');
  document.querySelectorAll('.donate-amounts button').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.donate-amounts button').forEach(function (x) { x.classList.remove('active'); });
      b.classList.add('active');
      if (amountInput) amountInput.value = b.getAttribute('data-amount');
    });
  });

  /* ---------- Newsletter (front-end only) ---------- */
  var nf = document.querySelector('.newsletter-form');
  if (nf) {
    nf.addEventListener('submit', function (e) {
      e.preventDefault();
      var msg = document.querySelector('.form-msg');
      if (msg) msg.textContent = 'Thank you! You are subscribed to weekly encouragement.';
      nf.reset();
    });
  }

  /* ---------- Hero video: skip the black intro and loop from there ---------- */
  var heroVideo = document.querySelector('.hero-video');
  if (heroVideo) {
    var START = 3.5; // seconds of black fade-in at the start of the clip
    heroVideo.loop = false; // looping is handled below so it restarts after the intro
    var stillOnly = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (stillOnly) heroVideo.removeAttribute('autoplay');
    var jumpToStart = function () {
      try { heroVideo.currentTime = START; } catch (e) {}
      if (stillOnly) { // "reduce motion" visitors see a still frame of the video
        heroVideo.pause();
        heroVideo.addEventListener('seeked', function () { heroVideo.classList.add('ready'); }, { once: true });
        return;
      }
      var p = heroVideo.play();
      if (p && p.catch) p.catch(function () {});
    };
    if (heroVideo.readyState >= 1) jumpToStart();
    else heroVideo.addEventListener('loadedmetadata', jumpToStart, { once: true });
    heroVideo.addEventListener('ended', jumpToStart);
    heroVideo.addEventListener('timeupdate', function () {
      if (heroVideo.currentTime >= START - 0.05) heroVideo.classList.add('ready');
    });
  }

  /* ---------- Events: ticket-card slider ---------- */
  var slider = document.querySelector('.events-slider');
  if (slider && slider.querySelectorAll('.ticket-card').length > 1 && slider.querySelector('.prev')) {
    var slides = slider.querySelectorAll('.ticket-card');
    var current = 0;
    var timer = null;
    var show = function (n) {
      current = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) {
        s.classList.toggle('is-active', i === current);
        s.setAttribute('aria-hidden', i === current ? 'false' : 'true');
        s.querySelectorAll('a').forEach(function (a) { a.tabIndex = i === current ? 0 : -1; });
      });
    };
    var auto = function () {
      clearInterval(timer);
      if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        timer = setInterval(function () { show(current + 1); }, 6000);
      }
    };
    slider.querySelector('.prev').addEventListener('click', function () { show(current - 1); auto(); });
    slider.querySelector('.next').addEventListener('click', function () { show(current + 1); auto(); });
    slider.addEventListener('mouseenter', function () { clearInterval(timer); });
    slider.addEventListener('mouseleave', auto);
    show(0);
    auto();
  }

  /* ---------- Events: calendar (marks every Saturday for Sabbath worship) ---------- */
  var cal = document.querySelector('[data-calendar]');
  if (cal) {
    var grid = cal.querySelector('[data-cal-grid]');
    var title = cal.querySelector('[data-cal-title]');
    var detail = cal.querySelector('[data-cal-detail]');
    var view = new Date();
    view.setDate(1);
    var today = new Date();
    var render = function () {
      var y = view.getFullYear(), m = view.getMonth();
      title.textContent = view.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' });
      var html = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(function (d) {
        return '<div class="dow" role="columnheader">' + d + '</div>';
      }).join('');
      var first = new Date(y, m, 1).getDay();
      var days = new Date(y, m + 1, 0).getDate();
      for (var i = 0; i < first; i++) html += '<div class="day empty" aria-hidden="true"></div>';
      for (var d = 1; d <= days; d++) {
        var date = new Date(y, m, d);
        var isSat = date.getDay() === 6;
        var isToday = date.toDateString() === today.toDateString();
        var label = date.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
        html += isSat
          ? '<button type="button" class="day sabbath' + (isToday ? ' today' : '') + '" data-label="' + label + '" aria-label="' + label + ', Sabbath Worship Service">' + d + '</button>'
          : '<div class="day' + (isToday ? ' today' : '') + '" role="gridcell">' + d + '</div>';
      }
      grid.innerHTML = html;
      detail.textContent = 'Select a Saturday to see the service time.';
    };
    grid.addEventListener('click', function (e) {
      var b = e.target.closest('.day.sabbath');
      if (!b) return;
      grid.querySelectorAll('.selected').forEach(function (x) { x.classList.remove('selected'); });
      b.classList.add('selected');
      detail.textContent = b.getAttribute('data-label') + ' — Sabbath Worship Service, 9:00 AM to 2:00 PM (All Branches).';
    });
    cal.querySelector('[data-cal-prev]').addEventListener('click', function () { view.setMonth(view.getMonth() - 1); render(); });
    cal.querySelector('[data-cal-next]').addEventListener('click', function () { view.setMonth(view.getMonth() + 1); render(); });
    render();
  }

  /* ---------- Giving form (2 steps; shows how to pay, no online processing) ---------- */
  var give = document.querySelector('[data-give]');
  if (give) {
    var step1 = give.querySelector('[data-step="1"]');
    var step2 = give.querySelector('[data-step="2"]');
    var dots = give.querySelectorAll('.give-steps i');
    var titleEl = give.querySelector('[data-give-title]');
    var otherInput = give.querySelector('[data-other]');
    var currencySel = give.querySelector('[data-currency]');
    var amountBtns = give.querySelectorAll('[data-amt]');
    var freq = 'One-time';
    var amount = null;

    give.querySelectorAll('[data-freq]').forEach(function (b) {
      b.addEventListener('click', function () {
        freq = b.getAttribute('data-freq');
        give.querySelectorAll('[data-freq]').forEach(function (x) {
          x.classList.toggle('active', x === b);
          x.setAttribute('aria-checked', x === b ? 'true' : 'false');
        });
      });
    });
    amountBtns.forEach(function (b) {
      b.addEventListener('click', function () {
        amount = Number(b.getAttribute('data-amt'));
        otherInput.value = '';
        amountBtns.forEach(function (x) { x.classList.toggle('active', x === b); });
      });
    });
    otherInput.addEventListener('input', function () {
      amount = otherInput.value ? Number(otherInput.value) : null;
      amountBtns.forEach(function (x) { x.classList.remove('active'); });
    });
    currencySel.addEventListener('change', function () {
      give.querySelectorAll('[data-cur]').forEach(function (s) { s.textContent = currencySel.value; });
    });
    var toggle = give.querySelector('[data-comment-toggle]');
    var comment = give.querySelector('[data-comment]');
    toggle.addEventListener('change', function () { comment.hidden = !toggle.checked; if (toggle.checked) comment.focus(); });

    // Prefill from the homepage form (giving.html?amount=200)
    var preset = Number(new URLSearchParams(location.search).get('amount'));
    if (preset > 0) {
      var match = Array.prototype.find.call(amountBtns, function (b) { return Number(b.getAttribute('data-amt')) === preset; });
      if (match) match.click(); else { otherInput.value = preset; amount = preset; }
    }

    var esc = function (s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; };
    var showStep = function (n) {
      step1.hidden = n !== 1;
      step2.hidden = n !== 2;
      dots.forEach(function (d, i) { d.classList.toggle('on', i < n); });
      titleEl.textContent = n === 1 ? 'Choose amount' : 'Complete your gift';
    };

    step1.addEventListener('submit', function (e) {
      e.preventDefault();
      var err = give.querySelector('[data-error]');
      var designation = give.querySelector('[data-designation]').value;
      if (!amount || amount <= 0) { err.textContent = 'Please choose or enter an amount.'; return; }
      if (!designation) { err.textContent = 'Please choose a designation.'; return; }
      err.textContent = '';
      var cur = currencySel.value;
      var formatted = cur + ' ' + amount.toLocaleString('en-GB', { maximumFractionDigits: 2 });
      give.querySelector('[data-summary]').innerHTML =
        '<strong>' + esc(formatted) + '</strong>' +
        '<p>' + esc(freq) + ' · ' + esc(designation) + '</p>' +
        (comment.value.trim() && toggle.checked ? '<p>“' + esc(comment.value.trim()) + '”</p>' : '');
      // Copy the payment details from the page so they are only edited in one place
      give.querySelectorAll('[data-copy]').forEach(function (span) {
        var src = document.querySelector('[data-pay="' + span.getAttribute('data-copy') + '"]');
        span.textContent = src ? src.textContent.trim() : '';
        span.classList.toggle('tbc', !!(src && src.classList.contains('tbc')));
      });
      give.querySelector('[data-monthly-note]').hidden = freq !== 'Monthly';
      showStep(2);
    });
    give.querySelector('[data-back]').addEventListener('click', function () { showStep(1); });
  }

  /* ---------- Homepage: apostles curved gallery -> detail view ---------- */
  var ap = document.querySelector('[data-ap]');
  if (ap) {
    var apCards = Array.prototype.slice.call(ap.querySelectorAll('.ap-card'));
    var apDetail = ap.querySelector('[data-ap-detail]');
    var apBig = ap.querySelector('[data-ap-big]');
    var apName = ap.querySelector('[data-ap-name]');
    var apRole = ap.querySelector('[data-ap-role]');
    var apBio = ap.querySelector('[data-ap-bio]');
    var apThumbs = ap.querySelector('[data-ap-thumbs]');
    var lastCard = null;
    var photoOf = function (card) { return card.querySelector('.ap-photo').outerHTML; };
    var show = function (card, fromThumb) {
      lastCard = card;
      // Restart the entrance animations
      apDetail.hidden = true;
      void apDetail.offsetWidth;
      apBig.innerHTML = photoOf(card);
      apName.textContent = card.getAttribute('data-name');
      apRole.textContent = card.getAttribute('data-role');
      apBio.textContent = card.getAttribute('data-bio');
      apThumbs.innerHTML = '';
      apCards.forEach(function (c) {
        var t = document.createElement('button');
        t.type = 'button';
        t.className = 'ap-thumb' + (c === card ? ' is-current' : '');
        t.setAttribute('aria-label', c.getAttribute('data-name'));
        if (c === card) t.setAttribute('aria-current', 'true');
        t.innerHTML = photoOf(c);
        t.addEventListener('click', function () { show(c, true); });
        apThumbs.appendChild(t);
      });
      ap.classList.add('is-open');
      apDetail.hidden = false;
      if (fromThumb) {
        var cur = apThumbs.querySelector('.is-current');
        if (cur) cur.focus();
      } else {
        apName.focus({ preventScroll: true });
        var top = ap.getBoundingClientRect().top + window.scrollY - 140;
        if (window.scrollY > top) window.scrollTo({ top: top, behavior: reduceMotion ? 'auto' : 'smooth' });
      }
    };
    var close = function () {
      ap.classList.remove('is-open');
      apDetail.hidden = true;
      if (lastCard) lastCard.focus();
    };
    // Even out the *visible* gaps: turned cards look narrower than the space they occupy,
    // so measure their on-screen edges and nudge each card's right margin (desktop curve only).
    var GAP = 18;
    var spaceCards = function () {
      var desktop = window.matchMedia('(min-width: 992px)').matches;
      apCards.forEach(function (c) { c.style.marginRight = ''; });
      if (!desktop) return;
      var margins = apCards.map(function () { return 0; });
      for (var pass = 0; pass < 4; pass++) {
        var rects = apCards.map(function (c) { return c.getBoundingClientRect(); });
        for (var i = 0; i < apCards.length - 1; i++) {
          margins[i] += GAP - (rects[i + 1].left - rects[i].right);
          apCards[i].style.marginRight = margins[i].toFixed(2) + 'px';
        }
      }
    };
    spaceCards();
    var spaceTimer;
    var respace = function () { clearTimeout(spaceTimer); spaceTimer = setTimeout(spaceCards, 120); };
    window.addEventListener('resize', respace);
    if ('ResizeObserver' in window) {
      var lastW = 0;
      new ResizeObserver(function (entries) {
        var w = Math.round(entries[0].contentRect.width);
        if (w !== lastW) { lastW = w; respace(); }
      }).observe(ap.querySelector('[data-ap-curve]'));
    }

    apCards.forEach(function (c) { c.addEventListener('click', function () { show(c, false); }); });
    ap.querySelector('[data-ap-back]').addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && ap.classList.contains('is-open')) close();
    });
  }

  /* ---------- Find a Church: detail slider card (01/03) ---------- */
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('[data-hq-slider]').forEach(function (box) {
    var items = box.querySelectorAll('.hq-slide');
    var counter = box.querySelector('[data-hq-current]');
    var bar = box.querySelector('[data-hq-progress]');
    var idx = 0;
    var restartBar = function () {
      if (!bar || reduceMotion) return;
      bar.classList.remove('run');
      void bar.offsetWidth; // restart the CSS animation
      bar.classList.add('run');
    };
    var go = function (n, dir) {
      var prev = idx;
      idx = (n + items.length) % items.length;
      // Set the travel direction first so the incoming slide starts on the correct side
      box.style.setProperty('--dir', dir < 0 ? '-1' : '1');
      items.forEach(function (s) { s.classList.remove('is-out'); });
      void box.offsetWidth;
      items.forEach(function (s, i) {
        var on = i === idx;
        s.classList.toggle('is-active', on);
        s.classList.toggle('is-out', i === prev && !on);
        s.setAttribute('aria-hidden', on ? 'false' : 'true');
        s.querySelectorAll('a').forEach(function (a) { a.tabIndex = on ? 0 : -1; });
      });
      if (counter) {
        counter.textContent = (idx + 1 < 10 ? '0' : '') + (idx + 1);
        counter.classList.remove('tick');
        void counter.offsetWidth;
        counter.classList.add('tick');
      }
      restartBar();
    };
    box.querySelector('[data-hq-prev]').addEventListener('click', function () { go(idx - 1, -1); });
    box.querySelector('[data-hq-next]').addEventListener('click', function () { go(idx + 1, 1); });
    // Auto-play: when the progress line finishes (it pauses on hover/focus), move on
    if (bar) bar.addEventListener('animationend', function () { go(idx + 1, 1); });
    items.forEach(function (s, i) { s.setAttribute('aria-hidden', i === 0 ? 'false' : 'true'); });
    restartBar();
  });

  /* ---------- Regional & District Events (data: assets/js/events-data.js) ---------- */
  var evData = window.TFCI_EVENTS || {};
  var evEsc = function (s) { var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; };
  var evSafeUrl = function (u) { return /^(https?:\/\/|assets\/|[\w-]+\.html)/i.test(u || '') ? u : ''; };
  var evCard = function (ev) {
    var link = evSafeUrl(ev.link);
    var img = evSafeUrl(ev.image);
    var tag = link ? 'a' : 'article';
    var attrs = link ? ' href="' + evEsc(link) + '"' + (/^https?:/i.test(link) ? ' target="_blank" rel="noopener"' : '') : '';
    return '<' + tag + ' class="past-event-card"' + attrs + '>' +
      '<figure class="past-event-image">' +
        (img ? '<img src="' + evEsc(img) + '" alt="" loading="lazy">' : '<span class="events-noimage"><i class="fa-regular fa-calendar"></i></span>') +
      '</figure>' +
      '<div class="past-event-info">' +
        '<p class="past-event-date"><i class="fa-regular fa-calendar"></i>' + evEsc(ev.date || 'Date to be confirmed') + '</p>' +
        '<h3>' + evEsc(ev.title) + '</h3>' +
        (ev.place ? '<p class="past-event-place"><i class="fa-solid fa-location-dot"></i>' + evEsc(ev.place) + '</p>' : '') +
      '</div>' +
    '</' + tag + '>';
  };
  // "region:ashanti-east" -> { upcoming: [...], past: [...] }
  var evFor = function (key) {
    var parts = (key || '').split(':');
    var isRegion = parts[0] === 'region';
    var up = (isRegion ? evData.regionalEvents : evData.districtEvents) || {};
    var past = (isRegion ? evData.regionalPastEvents : evData.districtPastEvents) || {};
    return { region: isRegion, upcoming: up[parts[1]] || [], past: past[parts[1]] || [] };
  };

  // An area page: past events replace the placeholder cards once some are added
  document.querySelectorAll('[data-area-past]').forEach(function (grid) {
    var past = evFor(grid.getAttribute('data-area-past')).past;
    if (past.length) grid.innerHTML = past.map(evCard).join('');
  });

  // Overview hero slides: show an area's next upcoming event when there is one
  document.querySelectorAll('[data-area-slide]').forEach(function (slide) {
    var next = evFor(slide.getAttribute('data-area-slide')).upcoming[0];
    if (!next) return;
    var name = slide.querySelector('[data-slide-title]').textContent;
    slide.querySelector('[data-slide-title]').textContent = next.title;
    slide.querySelector('[data-slide-sub]').textContent = name + (next.place ? ' · ' + next.place : '');
    slide.querySelector('[data-slide-meta]').innerHTML =
      '<li><i class="fa-regular fa-calendar"></i>' + evEsc(next.date || 'Date to be confirmed') + '</li>' +
      (next.place ? '<li><i class="fa-solid fa-location-dot"></i>' + evEsc(next.place) + '</li>' : '');
    if (evSafeUrl(next.image)) slide.querySelector('.ticket-img img').src = next.image;
  });

  // Overview cards: how many events (upcoming + past) each area has
  document.querySelectorAll('[data-area-count]').forEach(function (el) {
    var ev = evFor(el.getAttribute('data-area-count'));
    var n = ev.upcoming.length + ev.past.length;
    el.textContent = n ? n + (n === 1 ? ' event' : ' events') : 'No events yet';
  });

  /* ---------- Contact form: opens the visitor's email app (no server) ---------- */
  var cf = document.querySelector('.contact-form');
  if (cf) {
    cf.addEventListener('submit', function (e) {
      e.preventDefault();
      var note = cf.querySelector('.contact-form-note');
      var missing = [];
      cf.querySelectorAll('[required]').forEach(function (f) {
        var bad = !f.value.trim() || (f.type === 'email' && !f.checkValidity());
        f.classList.toggle('invalid', bad);
        if (bad) missing.push(f);
      });
      if (missing.length) {
        note.textContent = 'Please fill in your name, a valid email address and your message.';
        note.classList.add('error');
        missing[0].focus();
        return;
      }
      var v = function (n) { return cf.elements[n].value.trim(); };
      var name = v('first') + ' ' + v('last');
      var body = v('message') + '\n\n' + name + '\nEmail: ' + v('email') + (v('phone') ? '\nPhone: ' + v('phone') : '');
      note.classList.remove('error');
      note.textContent = 'Opening your email app…';
      window.location.href = 'mailto:' + cf.getAttribute('data-mailto') +
        '?subject=' + encodeURIComponent('Message from ' + name + ' (website)') +
        '&body=' + encodeURIComponent(body);
    });
  }

  /* ---------- Footer year ---------- */
  document.querySelectorAll('.js-year').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
