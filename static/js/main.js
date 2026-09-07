// Main Client Script
document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss flash alerts after 5 seconds
    const flashAlerts = document.querySelectorAll(".flash-alert");
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = "0";
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });
});
