/**
 * story_timeline.js — Interactive handlers for Attack Story timeline and details.
 */
document.addEventListener("DOMContentLoaded", function () {
    // Smooth toggling and styling for timeline details
    const timelineItems = document.querySelectorAll(".story-timeline .timeline-item");
    timelineItems.forEach(item => {
        const details = item.querySelector("details");
        if (details) {
            details.addEventListener("toggle", function () {
                if (details.open) {
                    item.classList.add("expanded");
                } else {
                    item.classList.remove("expanded");
                }
            });
        }
    });
});
