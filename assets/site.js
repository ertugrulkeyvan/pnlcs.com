// pnlcs.com — small progressive enhancements. Every page reads fine without JS;
// numbers in [data-stat] are build-time fallbacks that get refreshed from GitHub / Docker Hub.
(function () {
  'use strict';
  var REPO = 'Panelica/pnlcs';
  var T = window.PNLCS_I18N || {};
  var L = function (key, fallback, vars) {
    var s = T[key] || fallback;
    Object.keys(vars || {}).forEach(function (k) { s = s.replace('{' + k + '}', vars[k]); });
    return s;
  };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  // ---------- Header: mobile menu + dropdowns ----------
  var header = document.querySelector('.site-header');
  var menuBtn = document.querySelector('.menu-btn');
  var triggers = $$('.nav-trigger');
  var desktop = window.matchMedia('(min-width: 1101px)');
  var hover = window.matchMedia('(hover: hover) and (pointer: fine)');

  var setOpen = function (trigger, open) {
    trigger.setAttribute('aria-expanded', String(open));
    document.getElementById(trigger.getAttribute('aria-controls')).classList.toggle('is-open', open);
  };
  var closeAll = function (except) {
    triggers.forEach(function (t) { if (t !== except) setOpen(t, false); });
  };

  triggers.forEach(function (t) {
    var item = t.parentElement;
    var menu = document.getElementById(t.getAttribute('aria-controls'));
    if (menu.querySelector('[aria-current="page"]')) t.classList.add('is-current');
    t.addEventListener('click', function () {
      var open = t.getAttribute('aria-expanded') !== 'true';
      closeAll(t);
      setOpen(t, open);
    });
    var timer;
    item.addEventListener('mouseenter', function () {
      if (!desktop.matches || !hover.matches) return;
      clearTimeout(timer); closeAll(t); setOpen(t, true);
    });
    item.addEventListener('mouseleave', function () {
      if (!desktop.matches || !hover.matches) return;
      timer = setTimeout(function () { setOpen(t, false); }, 180);
    });
  });
  document.addEventListener('click', function (e) {
    if (desktop.matches && !e.target.closest('.nav-item')) closeAll();
    $$('details.lang[open]').forEach(function (d) { if (!d.contains(e.target)) d.removeAttribute('open'); });
  });
  // A language picked here wins over the browser's language (see lang_redirect in build.py)
  $$('.lang a[data-lang]').forEach(function (a) {
    a.addEventListener('click', function () {
      try { localStorage.setItem('pnlcs-lang', a.getAttribute('data-lang')); } catch (e) {}
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var open = triggers.filter(function (t) { return t.getAttribute('aria-expanded') === 'true'; })[0];
    if (open) { setOpen(open, false); open.focus(); }
  });

  if (header && menuBtn) {
    menuBtn.addEventListener('click', function () {
      var open = header.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.textContent = open ? L('close', 'Close') : L('menu', 'Menu');
      if (!open) closeAll();
    });
  }

  // ---------- Live project status ----------
  var setStat = function (name, value) {
    $$('[data-stat="' + name + '"]').forEach(function (el) { el.textContent = value; });
  };
  // Remote JSON is cached for an hour in sessionStorage: the GitHub API allows 60 anonymous
  // requests per hour per visitor, and every page asks for the same few numbers.
  var TTL = 3600000;
  var json = function (url) {
    var remote = /^https?:/.test(url);
    if (remote) {
      try {
        var hit = JSON.parse(sessionStorage.getItem('pnlcs:' + url) || 'null');
        if (hit && Date.now() - hit.t < TTL) return Promise.resolve(hit.d);
      } catch (e) {}
    }
    return fetch(url).then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); }).then(function (d) {
      if (remote) { try { sessionStorage.setItem('pnlcs:' + url, JSON.stringify({ t: Date.now(), d: d })); } catch (e) {} }
      return d;
    });
  };

  // The repository numbers come from shields.io (cached there, no per-visitor limit), so the GitHub API's
  // 60 requests an hour per address is left for the contributors list below.
  if (document.querySelector('[data-stat]')) {
    var shields = { stars: 'github/stars/', forks: 'github/forks/', issues: 'github/issues/', release: 'github/v/release/' };
    Object.keys(shields).forEach(function (name) {
      if (!document.querySelector('[data-stat="' + name + '"]')) return;
      json('https://img.shields.io/' + shields[name] + REPO + '.json').then(function (d) {
        if (d && d.value && !/invalid|inaccessible|not found/i.test(d.value)) setStat(name, String(d.value).split(' ')[0]);
      }).catch(function () {});
    });
    json('https://img.shields.io/docker/pulls/panelica/pnlcs-runtime.json').then(function (d) {
      if (d && d.value) setStat('pulls', d.value);
    }).catch(function () {});
  }

  // Contributors: count everywhere, full wall where #contributors exists
  var wall = document.getElementById('contributors');
  var avatars = document.querySelector('[data-avatars]');
  if (wall || avatars || document.querySelector('[data-stat="contributors"]')) {
    json('https://api.github.com/repos/' + REPO + '/contributors?per_page=100').then(function (list) {
      var people = (Array.isArray(list) ? list : []).filter(function (c) { return c.type === 'User'; });
      if (!people.length) return;
      setStat('contributors', String(people.length));
      if (avatars) {
        avatars.innerHTML = people.slice(0, 6).map(function (c) {
          return '<img src="' + c.avatar_url + '&s=56" alt="" width="28" height="28" loading="lazy">';
        }).join('');
      }
      if (!wall) return;
      var community = people.filter(function (c) { return c.login !== 'Panelica'; });
      wall.innerHTML = community.map(function (c) {
        var n = c.contributions;
        return '<li><a href="' + c.html_url + '"><img src="' + c.avatar_url + '&s=68" alt="" width="34" height="34" loading="lazy">' +
          '<span><b>' + c.login + '</b><small>' + n + ' ' + (n === 1 ? L('contribution', 'contribution') : L('contributions', 'contributions')) + '</small></span></a></li>';
      }).join('');
    }).catch(function () {});
  }

  // ---------- Product window tabs (WAI-ARIA tabs) ----------
  var tablist = document.querySelector('.product-tabs');
  if (tablist) {
    var tabs = $$('[role="tab"]', tablist);
    var img = document.getElementById('product-img');
    var url = document.getElementById('product-url');
    var caption = document.getElementById('product-caption');
    var panel = document.getElementById('product-panel');
    var select = function (tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
      });
      img.src = tab.dataset.src;
      img.srcset = tab.dataset.srcset;
      img.alt = tab.dataset.alt;
      url.textContent = tab.dataset.url;
      caption.textContent = tab.dataset.caption;
      panel.setAttribute('aria-labelledby', tab.id);
      if (focus) tab.focus();
    };
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { select(tab); });
      tab.addEventListener('keydown', function (e) {
        var next = null;
        if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
        if (e.key === 'ArrowLeft') next = tabs[(i - 1 + tabs.length) % tabs.length];
        if (e.key === 'Home') next = tabs[0];
        if (e.key === 'End') next = tabs[tabs.length - 1];
        if (next) { e.preventDefault(); select(next, true); }
      });
    });
  }

  // ---------- Feature tour (vertical tabs, arrow keys move) ----------
  var tourTabs = $$('.tour-tab');
  if (tourTabs.length) {
    var tImg = document.getElementById('tour-img');
    var tPanel = document.getElementById('tour-panel');
    var pick = function (tab, focus) {
      tourTabs.forEach(function (x) { var on = x === tab; x.setAttribute('aria-selected', String(on)); x.tabIndex = on ? 0 : -1; });
      tImg.src = tab.dataset.src; tImg.srcset = tab.dataset.srcset; tImg.alt = tab.dataset.alt;
      tPanel.setAttribute('aria-labelledby', tab.id);
      if (focus) tab.focus();
    };
    tourTabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { pick(tab); });
      tab.addEventListener('keydown', function (e) {
        var n = null;
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') n = tourTabs[(i + 1) % tourTabs.length];
        if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') n = tourTabs[(i - 1 + tourTabs.length) % tourTabs.length];
        if (n) { e.preventDefault(); pick(n, true); }
      });
    });
  }

  // ---------- Showcase carousel: story-style progress bars, arrows, swipe, pause ----------
  $$('[data-carousel]').forEach(function (root) {
    var track = root.querySelector('.sc-track');
    var slides = $$('.sc-slide', root);
    var bars = $$('.sc-bar', root);
    var toggle = root.querySelector('.sc-toggle');
    var n = slides.length, i = 0;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var userPaused = reduce, hoverPaused = false;
    root.style.setProperty('--sc-dur', (+root.dataset.interval || 6500) + 'ms');

    var sync = function () {
      var paused = userPaused || hoverPaused;
      root.classList.toggle('is-paused', paused);
      toggle.setAttribute('aria-label', userPaused ? L('play', 'Play') : L('pause', 'Pause'));
    };
    var go = function (to) {
      i = (to + n) % n;
      track.style.transform = 'translateX(' + (-100 * i) + '%)';
      slides.forEach(function (s, k) {
        var on = k === i;
        s.setAttribute('aria-hidden', String(!on));
        $$('a, button', s).forEach(function (el) { el.tabIndex = on ? 0 : -1; });
      });
      bars.forEach(function (b, k) {
        b.classList.toggle('is-done', k < i);
        b.classList.remove('is-active');
        b.setAttribute('aria-current', String(k === i));
      });
      void bars[i].offsetWidth;  // restart the fill animation
      bars[i].classList.add('is-active');
    };

    root.addEventListener('animationend', function (e) {
      if (e.target.parentElement === bars[i]) go(i + 1);
    });
    root.querySelector('.sc-prev').addEventListener('click', function () { go(i - 1); });
    root.querySelector('.sc-next').addEventListener('click', function () { go(i + 1); });
    bars.forEach(function (b, k) { b.addEventListener('click', function () { go(k); }); });
    toggle.addEventListener('click', function () { userPaused = !userPaused; sync(); });
    root.addEventListener('mouseenter', function () { hoverPaused = true; sync(); });
    root.addEventListener('mouseleave', function () { hoverPaused = false; sync(); });
    root.addEventListener('focusin', function () { hoverPaused = true; sync(); });
    root.addEventListener('focusout', function (e) { if (!root.contains(e.relatedTarget)) { hoverPaused = false; sync(); } });
    var x0 = null;
    track.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    track.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) go(dx < 0 ? i + 1 : i - 1);
    });
    root.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') go(i + 1);
      if (e.key === 'ArrowLeft') go(i - 1);
    });
    go(0); sync();
  });

  // ---------- Theme preview: repaints the mini portal with each theme's real colours ----------
  var mini = document.querySelector('.mini');
  var pickers = document.querySelector('[data-theme-pickers]');
  if (mini && pickers) {
    var name = document.getElementById('theme-name');
    var desc = document.getElementById('theme-desc');
    var paint = function (t) {
      var c = t.colors;
      var vars = {
        '--t-nav': c.nav_bg || c.primary,
        '--t-h1': c.hero_bg_start, '--t-h2': c.hero_bg_mid, '--t-h3': c.hero_bg_end,
        '--t-primary': c.primary,
        '--t-accent': c.welcome_accent || c.accent,
        '--t-footer': c.footer_bg || c.nav_bg,
        '--t-body': c.body_bg || '#f5f6fa'
      };
      Object.keys(vars).forEach(function (k) { if (vars[k]) mini.style.setProperty(k, vars[k]); });
      name.textContent = t.name;
      desc.textContent = L('theme_colors', 'Primary {p}, accent {a}', { p: (c.primary || '').toUpperCase(), a: (c.welcome_accent || c.accent || '').toUpperCase() });
    };
    json(pickers.dataset.src).then(function (themes) {
      var list = pickers.dataset.themePickers === 'list';
      var wall = pickers.dataset.themePickers === 'wall';
      pickers.innerHTML = themes.map(function (t, i) {
        var c = t.colors;
        var style = '--a:' + (c.nav_bg || c.primary) + ';--b:' + (c.welcome_accent || c.accent);
        var pressed = t.slug === 'panelica' ? 'true' : 'false';
        if (wall) {
          var shot = '<span class="tw-shot" aria-hidden="true">' +
            '<i class="tw-nav" style="background:' + (c.nav_bg || c.primary) + '"></i>' +
            '<i class="tw-hero" style="background:linear-gradient(135deg,' + c.hero_bg_start + ',' + c.hero_bg_mid + ',' + c.hero_bg_end + ')"></i>' +
            '<i class="tw-body" style="background:' + (c.body_bg || '#f5f6fa') + '"></i>' +
            '<i class="tw-btn" style="background:' + (c.welcome_accent || c.accent) + '"></i></span>';
          return '<li><button type="button" aria-pressed="' + pressed + '" data-i="' + i + '">' + shot + '<span class="tw-name">' + t.name + '</span></button></li>';
        }
        if (list) {
          return '<li><button type="button" aria-pressed="' + pressed + '" data-i="' + i + '">' +
            '<i class="dot" style="' + style + '"></i><span><strong>' + t.name + '</strong><span>' + t.description + '</span></span></button></li>';
        }
        return '<button type="button" class="swatch" style="' + style + '" aria-pressed="' + pressed + '" data-i="' + i + '" aria-label="' + L('theme', '{name} theme', { name: t.name }) + '"></button>';
      }).join('');
      pickers.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-i]');
        if (!b) return;
        $$('button[data-i]', pickers).forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        paint(themes[+b.dataset.i]);
      });
      paint(themes.filter(function (t) { return t.slug === 'panelica'; })[0] || themes[0]);
    }).catch(function () {});
  }

  // ---------- Tabs that switch between panels (install commands per system) ----------
  $$('.tabs-list').forEach(function (list) {
    var tabs = $$('[role="tab"]', list);
    var show = function (tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
      });
      if (focus) tab.focus();
    };
    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { show(tab); });
      tab.addEventListener('keydown', function (e) {
        var n = null;
        if (e.key === 'ArrowRight') n = tabs[(i + 1) % tabs.length];
        if (e.key === 'ArrowLeft') n = tabs[(i - 1 + tabs.length) % tabs.length];
        if (e.key === 'Home') n = tabs[0];
        if (e.key === 'End') n = tabs[tabs.length - 1];
        if (n) { e.preventDefault(); show(n, true); }
      });
    });
  });

  // ---------- Copy buttons ----------
  $$('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (!navigator.clipboard) return;
      var text = document.getElementById(btn.dataset.copy).innerText.replace(/^\$ /gm, '');
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = L('copied', 'Copied');
        setTimeout(function () { btn.textContent = L('copy', 'Copy'); }, 1800);
      });
    });
  });

  // ---------- Cookie consent (defaults are set in <head>, before Tag Manager) ----------
  var banner = document.getElementById('consent');
  var stored = null;
  try { stored = JSON.parse(localStorage.getItem('pnlcs-consent')); } catch (e) {}
  if (banner) {
    if (!stored || stored.v !== 1) banner.hidden = false;
    $$('[data-consent]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var ok = btn.dataset.consent === 'accept', g = ok ? 'granted' : 'denied';
        try { localStorage.setItem('pnlcs-consent', JSON.stringify({ v: 1, ok: ok, t: new Date().toISOString() })); } catch (e) {}
        if (typeof window.gtag === 'function') {
          window.gtag('consent', 'update', { ad_storage: g, ad_user_data: g, ad_personalization: g, analytics_storage: g });
        }
        (window.dataLayer = window.dataLayer || []).push({ event: 'consent_update', consent_status: g });
        banner.hidden = true;
      });
    });
    $$('[data-consent-open]').forEach(function (btn) {
      btn.addEventListener('click', function () { banner.hidden = false; banner.querySelector('button').focus(); });
    });
  }

  // ---------- Discovery call form (Web3Forms) ----------
  $$('[data-lead-form]').forEach(function (form) {
    var status = form.querySelector('.form-status');
    var submit = form.querySelector('[type="submit"]');
    form.addEventListener('submit', function (e) {
      if (!window.fetch) return; // plain POST still works
      e.preventDefault();
      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = data[k] ? data[k] + ', ' + v : v; });
      data['Site language'] = document.documentElement.lang;
      data.Page = location.pathname;
      submit.disabled = true;
      status.className = 'form-status';
      status.textContent = L('form_sending', 'Sending…');
      fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(data) })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (!res.success) throw new Error(res.message);
          form.reset();
          status.className = 'form-status is-ok';
          status.textContent = L('form_sent', 'Thank you. Your request has been sent.');
          (window.dataLayer = window.dataLayer || []).push({ event: 'discovery_form_submit' });
        })
        .catch(function () {
          status.className = 'form-status is-error';
          status.textContent = L('form_error', 'The request could not be sent. Please try again.');
        })
        .then(function () { submit.disabled = false; });
    });
  });

  // ---------- Dates written as 2026-10-06 in the visitor's own format ----------
  $$('time[data-date]').forEach(function (t) {
    try {
      t.textContent = new Intl.DateTimeFormat(document.documentElement.lang, { year: 'numeric', month: 'short', day: 'numeric' })
        .format(new Date(t.getAttribute('datetime') + 'T12:00:00'));
    } catch (e) {}
  });

  // ---------- Modules and themes: search, filters, sort (every card is in the HTML; this only hides) ----------
  var groups = $$('#browse .xm-group');
  if (groups.length) {
    var side = document.getElementById('xm-filters');
    var fitSide = function () {
      var room = window.innerHeight - (parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-h')) || 72) - 40;
      side.classList.toggle('is-sticky', side.offsetHeight <= room);
    };
    if (window.ResizeObserver) new ResizeObserver(fitSide).observe(side);
    window.addEventListener('resize', fitSide);
    var search = document.getElementById('xm-q');
    var cards = $$('#browse .xc');
    var sortSel = document.querySelector('[data-xm-sort]');
    var countEl = document.querySelector('.xm-count');
    var activeEl = document.querySelector('.xm-active');
    var noneEl = document.querySelector('.xm-none');
    var filterBtn = document.querySelector('.xm-filter-btn');
    var badge = document.querySelector('.xm-badge');
    var chips = $$('[data-chip]');
    var MULTI = ['cat', 'price', 'pub', 'open'];
    $$('.xm-side, .xm-bar, .xm-chips').forEach(function (el) { el.hidden = false; });

    var norm = function (s) {
      return (s || '').toLocaleLowerCase().replace(/ı/g, 'i').normalize('NFD').replace(/[̀-ͯ]/g, '');
    };
    cards.forEach(function (c) { c._q = norm(c.dataset.q); });
    var inputs = function (name) { return $$('input[name="' + name + '"]', side); };
    var checked = function (name) { return inputs(name).filter(function (i) { return i.checked; }).map(function (i) { return i.value; }); };
    var labelOf = function (input) { return input.parentNode.querySelector('span').textContent.trim(); };

    var pubSet = document.querySelector('.xm-pub-filter');
    var moreBtn = document.querySelector('[data-xm-more]');
    if (pubSet && inputs('pub').length > 6) {
      pubSet.classList.add('is-collapsed');
      moreBtn.hidden = false;
      moreBtn.addEventListener('click', function () { pubSet.classList.remove('is-collapsed'); moreBtn.hidden = true; });
    }

    // state from the address, so a filtered view can be shared
    var params = new URLSearchParams(location.search);
    search.value = params.get('q') || '';
    var type = params.get('type') || '';
    inputs('type').forEach(function (i) { i.checked = i.value === type; });
    if (!checked('type').length) inputs('type')[0].checked = true;
    MULTI.forEach(function (name) {
      var wanted = (params.get(name) || '').split(',');
      inputs(name).forEach(function (i) { i.checked = wanted.indexOf(i.value) > -1 && !i.disabled; });
    });
    if (params.get('sort')) sortSel.value = params.get('sort');

    var apply = function () {
      var words = norm(search.value).split(/\s+/).filter(Boolean);
      var t = checked('type')[0] || '';
      var sel = {}; MULTI.forEach(function (n) { sel[n] = checked(n); });
      var shown = 0;
      cards.forEach(function (c) {
        var d = c.dataset;
        var ok = (!t || d.type === t) &&
          (!sel.cat.length || sel.cat.indexOf(d.cat) > -1) &&
          (!sel.price.length || sel.price.indexOf(d.price) > -1) &&
          (!sel.pub.length || sel.pub.indexOf(d.pub) > -1) &&
          (!sel.open.length || d.open === '1') &&
          words.every(function (w) { return c._q.indexOf(w) > -1; });
        c.hidden = !ok;
        if (ok) shown++;
      });
      var by = sortSel.value;
      cards.slice().sort(function (a, b) {
        if (by === 'name') return a.dataset.name.localeCompare(b.dataset.name);
        return b.dataset.updated.localeCompare(a.dataset.updated) || a.dataset.name.localeCompare(b.dataset.name);
      }).forEach(function (c) { c.parentNode.appendChild(c); });
      // with nothing narrowing the list, a long group shows its first rows and a button that opens the rest
      var browsing = !words.length && !t && MULTI.every(function (n) { return !sel[n].length; });
      groups.forEach(function (g) {
        var visible = $$('.xc', g).filter(function (c) { return !c.hidden; });
        var n = visible.length;
        var limit = g.dataset.group === 'theme' ? 6 : 9;
        var cut = browsing && groups.length > 1 && n > limit + 3;
        if (cut) visible.slice(limit).forEach(function (c) { c.hidden = true; });
        g.querySelector('.xm-group-more').hidden = !cut;
        g.hidden = !n;
        g.querySelector('.xm-group-n').textContent = n;
      });

      countEl.textContent = countEl.dataset.template.replace('{n}', shown).replace('{total}', cards.length);
      noneEl.hidden = shown > 0;

      // removable tags for everything that narrows the list
      var tags = [];
      if (words.length) tags.push({ label: L('search_for', 'Search: {q}', { q: search.value.trim() }), clear: function () { search.value = ''; } });
      if (t) {
        var ti = inputs('type').filter(function (i) { return i.checked; })[0];
        tags.push({ label: labelOf(ti), clear: function () { inputs('type')[0].checked = true; } });
      }
      MULTI.forEach(function (n) {
        inputs(n).filter(function (i) { return i.checked; }).forEach(function (i) {
          tags.push({ label: labelOf(i), clear: function () { i.checked = false; } });
        });
      });
      activeEl.innerHTML = '';
      tags.forEach(function (tag) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'xm-tag';
        b.setAttribute('aria-label', L('remove_filter', 'Remove filter: {name}', { name: tag.label }));
        b.innerHTML = '<span></span><svg class="ico" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>';
        b.firstChild.textContent = tag.label;
        b.addEventListener('click', function () { tag.clear(); apply(); });
        activeEl.appendChild(b);
      });
      activeEl.hidden = !tags.length;
      var n = tags.length - (words.length ? 1 : 0);
      badge.hidden = !n;
      badge.textContent = n;

      // category chips mirror the category checkboxes
      chips.forEach(function (ch) {
        var on = ch.dataset.chip ? sel.cat.length === 1 && sel.cat[0] === ch.dataset.chip : !sel.cat.length;
        ch.setAttribute('aria-pressed', String(on));
      });

      var q = new URLSearchParams();
      if (search.value.trim()) q.set('q', search.value.trim());
      if (t) q.set('type', t);
      MULTI.forEach(function (n) { if (sel[n].length) q.set(n, sel[n].join(',')); });
      if (by !== 'updated') q.set('sort', by);
      var qs = q.toString();
      history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
    };

    var clearAll = function () {
      search.value = '';
      inputs('type')[0].checked = true;
      MULTI.forEach(function (n) { inputs(n).forEach(function (i) { i.checked = false; }); });
      apply();
    };
    $$('.xm-group-more').forEach(function (btn) {
      btn.addEventListener('click', function () {
        inputs('type').forEach(function (i) { i.checked = i.value === btn.dataset.moreType; });
        apply();
        document.getElementById('browse').scrollIntoView({ behavior: 'smooth' });
      });
    });
    side.addEventListener('change', apply);
    sortSel.addEventListener('change', apply);
    search.addEventListener('input', apply);
    search.form.addEventListener('submit', function (e) {
      e.preventDefault();
      search.blur();
      document.getElementById('browse').scrollIntoView({ behavior: 'smooth' });
    });
    chips.forEach(function (ch) {
      ch.addEventListener('click', function () {
        inputs('cat').forEach(function (i) { i.checked = !!ch.dataset.chip && i.value === ch.dataset.chip; });
        apply();
      });
    });
    $$('[data-xm-clear]').forEach(function (b) { b.addEventListener('click', clearAll); });
    document.addEventListener('keydown', function (e) {
      if (e.key !== '/' || e.metaKey || e.ctrlKey || /input|textarea|select/i.test(e.target.tagName)) return;
      e.preventDefault();
      search.focus();
    });

    // narrow screens: the filters slide in from the side
    var scrim = null;
    var drawer = function (open) {
      side.classList.toggle('is-open', open);
      filterBtn.setAttribute('aria-expanded', String(open));
      document.body.style.overflow = open ? 'hidden' : '';
      if (open) {
        scrim = document.createElement('div');
        scrim.className = 'xm-scrim';
        scrim.addEventListener('click', function () { drawer(false); });
        document.body.appendChild(scrim);
        side.querySelector('input').focus();
      } else {
        if (scrim) scrim.remove();
        scrim = null;
        filterBtn.focus();
      }
    };
    filterBtn.addEventListener('click', function () { drawer(true); });
    $$('[data-xm-close]').forEach(function (b) { b.addEventListener('click', function () { drawer(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && side.classList.contains('is-open')) drawer(false); });

    apply();
  }

  // ---------- Listing screenshots: open larger, step through with the arrow keys ----------
  $$('[data-gallery]').forEach(function (gallery) {
    var dialog = gallery.nextElementSibling;
    if (!dialog || typeof dialog.showModal !== 'function') return;
    var shots = $$('.xd-shot img', gallery).map(function (img) { return img.getAttribute('src'); });
    var big = dialog.querySelector('img');
    var at = 0;
    var show = function (i) { at = (i + shots.length) % shots.length; big.src = shots[at]; };
    $$('.xd-shot', gallery).forEach(function (b, i) {
      b.addEventListener('click', function () { show(i); dialog.showModal(); });
    });
    var single = shots.length < 2;
    dialog.querySelector('.xd-lb-prev').hidden = single;
    dialog.querySelector('.xd-lb-next').hidden = single;
    dialog.querySelector('.xd-lb-prev').addEventListener('click', function () { show(at - 1); });
    dialog.querySelector('.xd-lb-next').addEventListener('click', function () { show(at + 1); });
    dialog.querySelector('.xd-lb-close').addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') show(at + 1);
      if (e.key === 'ArrowLeft') show(at - 1);
    });
  });
})();
