document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("dashboardSidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");

    if (!sidebar || !sidebarToggle) {
        return;
    }

    sidebarToggle.addEventListener("click", function () {
        sidebar.classList.toggle("is-open");
    });
});