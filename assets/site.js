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
  var ago = function (iso) {
    var days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
    if (days <= 0) return L('today', 'today');
    if (days === 1) return L('yesterday', 'yesterday');
    if (days < 30) return L('days_ago', '{n} days ago', { n: days });
    var months = Math.floor(days / 30);
    return months === 1 ? L('month_ago', 'a month ago') : L('months_ago', '{n} months ago', { n: months });
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

  if (document.querySelector('[data-stat]')) {
    json('https://api.github.com/repos/' + REPO).then(function (repo) {
      setStat('stars', repo.stargazers_count.toLocaleString('en'));
      setStat('forks', repo.forks_count.toLocaleString('en'));
      setStat('issues', repo.open_issues_count.toLocaleString('en'));
      setStat('pushed', ago(repo.pushed_at));
    }).catch(function () {});
    json('https://api.github.com/repos/' + REPO + '/releases/latest').then(function (rel) {
      setStat('release', rel.tag_name);
    }).catch(function () {});
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
})();
