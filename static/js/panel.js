document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('panel-nav-toggle');
    var sidebar = document.querySelector('.panel-sidebar');
    var backdrop = document.getElementById('panel-sidebar-backdrop');

    if (!toggle || !sidebar || !backdrop) {
        return;
    }

    function setOpen(open) {
        sidebar.classList.toggle('is-open', open);
        backdrop.hidden = !open;
        backdrop.setAttribute('aria-hidden', open ? 'false' : 'true');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        document.body.classList.toggle('panel-nav-open', open);
    }

    toggle.addEventListener('click', function () {
        setOpen(!sidebar.classList.contains('is-open'));
    });

    backdrop.addEventListener('click', function () {
        setOpen(false);
    });

    sidebar.querySelectorAll('.panel-nav a').forEach(function (link) {
        link.addEventListener('click', function () {
            setOpen(false);
        });
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && sidebar.classList.contains('is-open')) {
            setOpen(false);
        }
    });

    window.addEventListener('resize', function () {
        if (window.innerWidth > 768 && sidebar.classList.contains('is-open')) {
            setOpen(false);
        }
    });
});
