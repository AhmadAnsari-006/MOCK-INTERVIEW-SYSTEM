
function submitAnswer() {

    const answer = document.getElementById("answer").value;

    fetch("/answer", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            answer: answer
        })

    })

    .then(response => response.json())

    .then(data => {

        if (data.next_question) {

            document.getElementById("question-box").innerText =
                data.next_question;

            document.getElementById("answer").value = "";

        }

        else if (data.redirect) {

            window.location.href = data.redirect;

        }

    });

}
