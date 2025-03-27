let questions = [];
let currentIndex = 0;
let sessionId = localStorage.getItem("sessionId") || "";
let rightClickCount = 0; // Track the number of right button clicks
let selectedSet = null;

// Show overlay when page loads
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("question-set-overlay").style.display = "flex";

    // Ensure event listeners are only attached once
    document.getElementById("left-button").replaceWith(document.getElementById("left-button").cloneNode(true));
    document.getElementById("right-button").replaceWith(document.getElementById("right-button").cloneNode(true));

    document.getElementById("left-button").addEventListener("click", () => saveResponse("left"));
    document.getElementById("right-button").addEventListener("click", () => saveResponse("right"));
});

// Function to Select Question Set
function selectQuestionSet(setId) {
    selectedSet = setId;

    // Hide overlay
    document.getElementById("question-set-overlay").style.display = "none";

    // Fetch questions for the selected set
    fetch(`/fetch_questions?set_id=${setId}`)
        .then(response => response.json())
        .then(data => {
            console.log("✅ Fetched Questions:", data.length, data);
            if (!data || data.length === 0) {
                console.error("⚠ No questions received from server!");
                return;
            }
            questions = data;
            currentIndex = 0; // Reset index for new question set
            rightClickCount = 0; // Reset right click count
            loadQuestion();
        })
        .catch(error => console.error("❌ Fetch error:", error));
}

// Function to Load Next Question
function loadQuestion() {
    console.log(`❗️ Current Index: ${currentIndex} / Total Questions: ${questions.length}`);

    if (questions.length === 0) {
        console.error("⚠ No questions loaded yet!");
        return;
    }

    if (currentIndex < questions.length) {
        let q = questions[currentIndex];

        console.log("✅ Loading question:", q);

        // Clear previous content before updating
        document.getElementById("question-text").innerText = "";
        document.getElementById("left-text").innerText = "";
        document.getElementById("right-text").innerText = "";

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

// Function to Save Response
function saveResponse(choice) {
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
    console.log(`🟢 Before Update: Current Index = ${currentIndex}`);

    // Count right button clicks
    if (choice === "right") {
        rightClickCount++;
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

        console.log(`🔵 After Update: Current Index = ${currentIndex}`);

        // Ensure index only increments once
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

// Function to Determine the Result Page
function determineResultPage() {
    console.log(`📊 Final right clicks: ${rightClickCount}`);

    let pageNumber = Math.min(rightClickCount, 5); // Ensure max is 5
    let redirectPage = `/${pageNumber}.html`;

    console.log(`🔗 Redirecting to: ${redirectPage}`);
    window.location.href = redirectPage;
}