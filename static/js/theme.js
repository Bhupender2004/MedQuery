document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (!toggleBtn) return;

    const icon = toggleBtn.querySelector('.theme-icon');

    function updateToggleUI(theme) {
        if (theme === 'light') {
            icon.textContent = '🌙';
            toggleBtn.setAttribute('title', 'Switch to Dark Mode');
            toggleBtn.setAttribute('aria-label', 'Switch to Dark Mode');
        } else {
            icon.textContent = '☀️';
            toggleBtn.setAttribute('title', 'Switch to Light Mode');
            toggleBtn.setAttribute('aria-label', 'Switch to Light Mode');
        }
    }

    const currentTheme = localStorage.getItem('theme') || 'dark';
    updateToggleUI(currentTheme);

    toggleBtn.addEventListener('click', () => {
        const isLight = document.documentElement.classList.contains('light-theme');
        if (isLight) {
            document.documentElement.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
            updateToggleUI('dark');
        } else {
            document.documentElement.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
            updateToggleUI('light');
        }
    });
});
