/**
 * Privacy-Pac Quiz Logic
 * Author: ngeorge4
 * Current Date: 2025-03-20 04:44:43 UTC
 */

let questions = [];
let currentIndex = 0;
let sessionId = localStorage.getItem("sessionId") || "";
let rightClickCount = 0;
let selectedSet = null;
let gpioEnabled = false;

document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("question-set-overlay").style.display = "flex";
    gpioEnabled = document.body.getAttribute("data-gpio-enabled") === "true";

    // Setup basic button listeners
    document.getElementById("left-button").replaceWith(document.getElementById("left-button").cloneNode(true));
    document.getElementById("right-button").replaceWith(document.getElementById("right-button").cloneNode(true));

    // Add button listeners after DOM is loaded
    const leftButton = document.getElementById("left-button");
    const rightButton = document.getElementById("right-button");

    if (leftButton && rightButton) {
        leftButton.addEventListener("click", () => handleResponse("left"));
        rightButton.addEventListener("click", () => handleResponse("right"));
    } else {
        console.error("Button elements not found!");
    }

    // Setup GPIO if enabled
    if (gpioEnabled) {
        setupGPIOListeners();
    }
});

function setupGPIOListeners() {
    console.log("Setting up GPIO listeners...");
    
    const eventSource = new EventSource('/gpio-events');

    eventSource.onmessage = function(event) {
        try {
            // Skip processing heartbeat messages
            if (event.data.includes("heartbeat")) {
                return;
            }

            console.log("Raw SSE data:", event.data);
            const data = JSON.parse(event.data);

            if (data.choice && (data.choice === "left" || data.choice === "right")) {
                console.log(`Processing GPIO button press: ${data.choice}`);
                
                // Trigger the corresponding button press
                handleResponse(data.choice);
                
                // Visual feedback
                const button = document.getElementById(`${data.choice}-button`);
                if (button) {
                    button.classList.add('active');
                    setTimeout(() => button.classList.remove('active'), 200);
                }
            }
        } catch (e) {
            if (!event.data.includes("heartbeat")) {
                console.error("Error parsing GPIO event:", e);
                console.error("Raw event data:", event.data);
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

function selectQuestionSet(setId) {
    selectedSet = setId;
    document.getElementById("question-set-overlay").style.display = "none";

    fetch(`/fetch_questions?set_id=${setId}`)
        .then(response => response.json())
        .then(data => {
            console.log("✅ Fetched Questions:", data.length, data);
            if (!data || data.length === 0) {
                console.error("⚠ No questions received from server!");
                return;
            }
            questions = data;
            currentIndex = 0;
            rightClickCount = 0;
            loadQuestion();
        })
        .catch(error => console.error("❌ Fetch error:", error));
}

function loadQuestion() {
    console.log(`❗️ Current Index: ${currentIndex} / Total Questions: ${questions.length}`);

    if (questions.length === 0) {
        console.error("⚠ No questions loaded yet!");
        return;
    }

    if (currentIndex < questions.length) {
        let q = questions[currentIndex];
        console.log("✅ Loading question:", q);

        // Clear previous content
        document.getElementById("question-text").innerText = "";
        document.getElementById("left-text").innerText = "";
        document.getElementById("right-text").innerText = "";

        // Update with new content
        setTimeout(() => {
            document.getElementById("question-text").innerText = q.question;
            document.getElementById("left-text").innerText = q.left_choice;
            document.getElementById("right-text").innerText = q.right_choice;
        }, 50);
    } else {
        console.log("✅ All questions answered, determining result...");
        determineResultPage();
    }
}

function handleResponse(choice) {
    console.log(`Handling response: ${choice}`);
    
    if (currentIndex >= questions.length) {
        console.error("⚠ No more questions available!");
        return;
    }

    let question = questions[currentIndex];
    if (!question || !question.id) {
        console.error("❌ Error: Missing question_id for question", currentIndex);
        return;
    }

    let requestBody = {
        question_id: question.id,
        choice: choice,
        session_id: sessionId || null
    };

    console.log("📩 Submitting response:", requestBody);

    // Update right click count
    if (choice === "right") {
        rightClickCount++;
        console.log(`Right clicks: ${rightClickCount}`);
    }

    fetch("/submit_response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (!sessionId) {
            sessionId = data.session_id;
            localStorage.setItem("sessionId", sessionId);
        }

        // Move to next question
        if (currentIndex < questions.length - 1) {
            currentIndex++;
            loadQuestion();
        } else {
            console.log("✅ All questions answered, determining result...");
            determineResultPage();
        }
    })
    .catch(error => console.error("❌ Error submitting response:", error));
}

function determineResultPage() {
    console.log(`📊 Final right clicks: ${rightClickCount}`);
    let pageNumber = Math.min(rightClickCount, 5);
    let redirectPage = `/${pageNumber}.html`;
    console.log(`🔗 Redirecting to: ${redirectPage}`);
    window.location.href = redirectPage;
}


// Auto-select set 2 for testing or faking 
document.addEventListener("DOMContentLoaded", () => setTimeout(() => selectQuestionSet(2), 100));