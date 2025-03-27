var elem = document.documentElement;

// Function to enter fullscreen mode
function openFullscreen() {
    if (elem.requestFullscreen) {
        elem.requestFullscreen();
    } else if (elem.webkitRequestFullscreen) { /* Safari */
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) { /* IE11 */
        elem.msRequestFullscreen();
    }
    localStorage.setItem("fullscreenActive", "true"); // Store fullscreen state
}

// Function to monitor fullscreen exit and reapply it
function checkFullscreen() {
    if (!document.fullscreenElement &&
        !document.webkitFullscreenElement &&
        !document.mozFullScreenElement &&
        !document.msFullscreenElement) {

        // If user navigates away, check if fullscreen was previously active
        if (localStorage.getItem("fullscreenActive") === "true") {
            setTimeout(() => {
                openFullscreen();
            }, 300); // Small delay to avoid flickering
        }
    }
}

// Run on every page load
document.addEventListener("DOMContentLoaded", () => {
    if (localStorage.getItem("fullscreenActive") === "true") {
        openFullscreen(); // Re-enter fullscreen
    }

    // Listen for fullscreen changes and restore if exited
    document.addEventListener("fullscreenchange", checkFullscreen);
    document.addEventListener("webkitfullscreenchange", checkFullscreen);
    document.addEventListener("mozfullscreenchange", checkFullscreen);
    document.addEventListener("MSFullscreenChange", checkFullscreen);
});
