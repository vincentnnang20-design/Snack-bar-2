// JavaScript personnalisé pour FriscoClub.
// Transition de page et effets globaux.

document.addEventListener('DOMContentLoaded', function () {
    document.body.classList.add('page-transition');

    const fadeDuration = 350;
    const pageLinks = Array.from(document.querySelectorAll('a[href]:not([target="_blank"]):not([download])'));

    pageLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) {
            return;
        }

        const url = new URL(href, window.location.href);
        if (url.origin !== window.location.origin) {
            return;
        }

        link.addEventListener('click', function (event) {
            if (event.defaultPrevented) {
                return;
            }
            if (url.pathname === window.location.pathname && url.hash) {
                return;
            }
            event.preventDefault();
            document.body.classList.add('page-transition-exit');
            setTimeout(function () {
                window.location.href = url.href;
            }, fadeDuration);
        });
    });
});
