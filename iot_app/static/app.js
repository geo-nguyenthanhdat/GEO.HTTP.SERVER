// Base JS file for handling authentication state
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token, role) {
    localStorage.setItem('token', token);
    if (role) localStorage.setItem('role', role);
}

function getRole() {
    return localStorage.getItem('role') || 'user';
}

function clearToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/login';
}

async function fetchWithAuth(url, options = {}) {
    const token = getToken();
    if (!token) {
        window.location.href = '/login';
        return;
    }
    
    if (!options.headers) {
        options.headers = {};
    }
    options.headers['Authorization'] = `Bearer ${token}`;
    
    const response = await fetch(url, options);
    if (response.status === 401) {
        clearToken();
    }
    return response;
}

document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (getToken() && logoutBtn) {
        if (getRole() === 'admin') {
            const ul = document.querySelector('.navbar-nav');
            if (ul) {
                const li = document.createElement('li');
                li.className = 'nav-item';
                li.innerHTML = '<a class="nav-link text-warning fw-bold" href="/admin">Admin Panel</a>';
                ul.insertBefore(li, ul.firstChild);
            }
        }
        logoutBtn.style.display = 'block';
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            clearToken();
        });
    }
});
