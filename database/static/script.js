let questions = [];
let currentIndex = 0;
let sessionId = localStorage.getItem("sessionId") || "";

fetch("/fetch_questions")
    .then(response => response.json())
    .then(data => {
        questions = data;
        loadQuestion();
    });

function loadQuestion() {
    if (currentIndex < questions.length) {
        let q = questions[currentIndex];
        document.getElementById('question-text').innerText = q.question;
    } else {
        window.location.href = "/completion"; // Redirect after all questions
    }
}

function saveResponse(choice) {
    let questionId = questions[currentIndex].id;

    fetch("/submit_response", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question_id: questionId, choice: choice, session_id: sessionId })
    }).then(response => response.json())
      .then(data => {
          if (!sessionId) {
              sessionId = data.session_id;
              localStorage.setItem("sessionId", sessionId);
          }
          currentIndex++;
          loadQuestion();
      });
}

document.getElementById("left-button").addEventListener("click", () => saveResponse("left"));
document.getElementById("right-button").addEventListener("click", () => saveResponse("right"));