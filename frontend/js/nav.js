function renderNav(active) {
  const user = TaskFlow.getUser();
  const links = [
    { href: "dashboard.html", label: "Tasks", key: "dashboard",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>' },
    { href: "analytics.html", label: "Analytics", key: "analytics",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="M18 17V9M13 17V5M8 17v-3"/></svg>' },
    { href: "status.html", label: "Service status", key: "status",
      icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>' },
  ];

  const linksHtml = links.map(l => `
    <a class="nav-link ${l.key === active ? "active" : ""}" href="${l.href}">
      ${l.icon}<span>${l.label}</span>
    </a>
  `).join("");

  const shell = document.getElementById("app-shell");
  shell.insertAdjacentHTML("afterbegin", `
    <nav class="sidenav">
      <div class="brand">
        <div class="brand-mark">TF</div>
        <div class="brand-name">TaskFlow</div>
      </div>
      <div class="nav-links">${linksHtml}</div>
      <div class="nav-footer">
        <div class="user-chip"><span class="dot"></span>${user ? user.username : "guest"}</div>
        <button class="logout-btn" id="logout-btn">Sign out</button>
      </div>
    </nav>
  `);

  document.getElementById("logout-btn").addEventListener("click", () => {
    TaskFlow.clearSession();
    window.location.href = "index.html";
  });
}
