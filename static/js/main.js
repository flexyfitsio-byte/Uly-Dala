// Общая логика для всех страниц: подтягиваем XP пользователя в шапку.
async function loadNavProfile() {
  try {
    const res = await fetch('/api/profile');
    if (!res.ok) return;
    const user = await res.json();
    const badge = document.getElementById('xpBadge');
    if (badge) badge.textContent = `(${user.xp} XP)`;
  } catch (e) {
    // тихо игнорируем — профиль не критичен для отображения страницы
  }
}

document.addEventListener('DOMContentLoaded', loadNavProfile);
