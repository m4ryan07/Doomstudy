// =============================================
//   DOOM STUDY — Matrix Rain + FX
// =============================================

// --- MATRIX RAIN ---
(function () {
    const canvas = document.getElementById('matrix-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let W, H, cols, drops;

    const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()_+-=[]{}|<>?/\\ドゥームスタディ死滅破壊';

    function init() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
        cols  = Math.floor(W / 18);
        drops = Array(cols).fill(1);
    }

    function draw() {
        ctx.fillStyle = 'rgba(2, 4, 8, 0.05)';
        ctx.fillRect(0, 0, W, H);

        ctx.font = '14px Share Tech Mono, monospace';

        drops.forEach((y, i) => {
            const char = CHARS[Math.floor(Math.random() * CHARS.length)];
            const x = i * 18;

            // Head char — bright red
            ctx.fillStyle = '#ff2d2d';
            ctx.fillText(char, x, y * 18);

            // Slightly behind — dim
            if (drops[i] > 1) {
                ctx.fillStyle = 'rgba(255,45,45,0.3)';
                ctx.fillText(CHARS[Math.floor(Math.random() * CHARS.length)], x, (y - 1) * 18);
            }

            if (y * 18 > H && Math.random() > 0.975) drops[i] = 0;
            drops[i]++;
        });
    }

    init();
    window.addEventListener('resize', init);
    setInterval(draw, 50);
})();


// --- TYPING CURSOR on input focus ---
(function () {
    const inputs = document.querySelectorAll('.terminal-input, .terminal-textarea');
    inputs.forEach(el => {
        el.addEventListener('focus', () => el.parentElement.classList.add('focused'));
        el.addEventListener('blur',  () => el.parentElement.classList.remove('focused'));
    });
})();


// --- CARD ENTRANCE ANIMATION (stagger on load) ---
(function () {
    const cards = document.querySelectorAll('.question-card, .result-card');
    cards.forEach((card, i) => {
        card.style.animationDelay = `${i * 0.15}s`;
    });
})();