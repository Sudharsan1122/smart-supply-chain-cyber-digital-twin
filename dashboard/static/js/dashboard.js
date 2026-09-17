(function () {
    "use strict";
    const cfg = window.DASHBOARD || { refreshSeconds: 5 };
    if (cfg.refreshSeconds > 0) {
        setTimeout(function () { window.location.reload(); }, cfg.refreshSeconds * 1000);
    }
    const badge = document.getElementById("refresh-badge");
    if (badge) {
        let n = cfg.refreshSeconds;
        const t = setInterval(() => {
            n -= 1;
            if (n <= 0) { clearInterval(t); return; }
            badge.textContent = "auto-refresh " + n + "s";
        }, 1000);
    }
})();
