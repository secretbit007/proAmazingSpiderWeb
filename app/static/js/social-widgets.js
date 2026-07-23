(function () {
  'use strict';

  var SHARE_TEXT = 'proAmazingSpider — Spider Solitaire for Android & iPhone';

  var LINKS = {
    email: 'mailto:normand.maclaurin@gmail.com',
    playStore: 'https://play.google.com/store/apps/details?id=com.Mamre.proAmazingSpider',
    appStore: 'https://apps.apple.com/us/app/proamazingspider/id6769407076',
    youtube: 'https://www.youtube.com/watch?v=udhOnFEOQlc',
    reddit: 'https://www.reddit.com/r/proamazingspider/',
    discord: 'https://discord.gg/E7naGZ5US4',
  };

  /** Optional profile links — uncomment or add entries when you have accounts. */
  var FOLLOW = [
    { href: LINKS.youtube, icon: 'ti-youtube', label: 'YouTube', external: true },
    { href: LINKS.reddit, icon: 'ti-reddit', label: 'Reddit community', external: true },
    { href: LINKS.discord, icon: 'icon-discord', label: 'Discord server', external: true },
  ];

  var CONNECT = [
    { href: LINKS.email, icon: 'ti-email', label: 'Email us' },
    { href: LINKS.playStore, icon: 'ti-android', label: 'Google Play', external: true },
    { href: LINKS.appStore, icon: 'ti-apple', label: 'App Store', external: true },
  ];

  function externalAttrs(item) {
    return item.external ? ' target="_blank" rel="noopener noreferrer"' : '';
  }

  function iconList(items, extraClass) {
    if (!items.length) {
      return '';
    }
    var lis = items
      .map(function (item) {
        return (
          '<li class="social-widgets__item">' +
          '<a href="' +
          item.href +
          '" class="social-widgets__icon"' +
          externalAttrs(item) +
          ' aria-label="' +
          item.label +
          '">' +
          '<i class="' +
          item.icon +
          '" aria-hidden="true"></i>' +
          '</a></li>'
        );
      })
      .join('');
    return (
      '<ul class="social-widgets__icons list-inline mb-0' +
      (extraClass ? ' ' + extraClass : '') +
      '">' +
      lis +
      '</ul>'
    );
  }

  function shareItems() {
    var url = encodeURIComponent(window.location.href);
    var text = encodeURIComponent(SHARE_TEXT);
    return [
      {
        href: 'https://www.facebook.com/sharer/sharer.php?u=' + url,
        icon: 'ti-facebook',
        label: 'Share on Facebook',
        external: true,
      },
      {
        href: 'https://twitter.com/intent/tweet?url=' + url + '&text=' + text,
        icon: 'ti-twitter',
        label: 'Share on X',
        external: true,
      },
      {
        href: 'https://www.linkedin.com/sharing/share-offsite/?url=' + url,
        icon: 'ti-linkedin',
        label: 'Share on LinkedIn',
        external: true,
      },
      {
        href: 'mailto:?subject=' + encodeURIComponent(SHARE_TEXT) + '&body=' + url,
        icon: 'ti-sharethis',
        label: 'Share by email',
      },
    ];
  }

  function renderBlock(container, variant) {
    var connectItems = CONNECT.concat(FOLLOW);
    var html = '';

    html += '<div class="social-widgets__group">';
    html += '<p class="social-widgets__title">Connect</p>';
    html += iconList(connectItems);
    html += '</div>';

    html += '<div class="social-widgets__group">';
    html += '<p class="social-widgets__title">Share this page</p>';
    html += iconList(shareItems(), 'social-widgets__icons--share');
    html += '</div>';

    container.innerHTML = html;
    container.classList.add('social-widgets--ready');
    if (variant === 'contact') {
      container.classList.add('social-widgets--contact');
    } else {
      container.classList.add('social-widgets--footer');
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-social-widgets]').forEach(function (el) {
      renderBlock(el, el.getAttribute('data-social-widgets') || 'footer');
    });
  });
})();
