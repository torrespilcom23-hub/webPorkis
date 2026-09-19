(function () {
    var STORAGE_KEY = 'porkis_dashboard_solo_alertas';
    var page = document.querySelector('.dashboard-page');
    var toggle = document.getElementById('dashboard-solo-alertas');
    var allClear = document.getElementById('dashboard-all-clear');

    if (!page || !toggle) {
        return;
    }

    function readSoloAlertas() {
        var stored = localStorage.getItem(STORAGE_KEY);
        if (stored === null) {
            return true;
        }
        return stored === '1';
    }

    function hasAlertPanels() {
        return page.querySelector('.dashboard-panel[data-has-alert="true"]') !== null;
    }

    function updateAllClear(solo) {
        if (!allClear) {
            return;
        }
        var show = solo && !hasAlertPanels();
        allClear.hidden = !show;
    }

    function applyMode(solo) {
        page.classList.toggle('dashboard-page--solo-alertas', solo);
        toggle.checked = solo;
        localStorage.setItem(STORAGE_KEY, solo ? '1' : '0');
        updateAllClear(solo);
    }

    toggle.addEventListener('change', function () {
        applyMode(toggle.checked);
    });

    applyMode(readSoloAlertas());
})();
