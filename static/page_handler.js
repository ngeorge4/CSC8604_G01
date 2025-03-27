document.addEventListener("DOMContentLoaded", function() {
    // Skip if we're on the quiz page
    if (window.location.pathname === '/quiz') {
        return;
    }

    // Add transition class to body after load
    document.body.classList.add('page-loaded');

    // Setup GPIO if enabled
    if (document.body.getAttribute("data-gpio-enabled") === "true") {
        setupGPIOListeners();
    }

    // Setup click handlers
    setupButtonHandlers();
});

function setupGPIOListeners() {
    console.log("Setting up GPIO listeners for navigation...");
    
    const eventSource = new EventSource('/gpio-events');

    eventSource.onmessage = function(event) {
        try {
            if (event.data.includes("heartbeat")) return;

            const data = JSON.parse(event.data);
            console.log("Navigation GPIO event:", data);

            if (data.choice) {
                handleButtonPress(data.choice);
            }
        } catch (e) {
            if (!event.data.includes("heartbeat")) {
                console.error("Navigation GPIO error:", e);
            }
        }
    };

    eventSource.onerror = function(error) {
        console.error("GPIO EventSource error:", error);
        setTimeout(setupGPIOListeners, 5000);
    };

    eventSource.onopen = function() {
        console.log("GPIO EventSource connected");
    };
}

function setupButtonHandlers() {
    // Handle button clicks with debouncing
    document.querySelectorAll('[data-gpio]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const direction = button.getAttribute('data-gpio');
            handleButtonPress(direction);
        });
    });
}

// Separate button press handling from navigation
function handleButtonPress(direction) {
    // Prevent multiple presses
    if (document.body.classList.contains('navigating')) {
        return;
    }

    const button = document.querySelector(`[data-gpio="${direction}"]`);
    if (button) {
        // Add pressed state
        button.classList.add('active');
        document.body.classList.add('navigating');

        // Handle navigation with transition
        handleNavigation(direction, button);
    }
}

function handleNavigation(choice, button) {
    console.log(`Handling navigation for ${choice} button`);

    fetch('/handle-navigation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_page: window.location.pathname,
            choice: choice
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.redirect) {
            // Start page transition
            document.body.classList.add('page-transitioning');
            
            // Remove active state after animation
            setTimeout(() => {
                button?.classList.remove('active');
                
                // Navigate after button animation
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 100);
            }, 200);
        }
    })
    .catch(error => {
        console.error('Navigation error:', error);
        document.body.classList.remove('navigating');
        button?.classList.remove('active');
    });
}
