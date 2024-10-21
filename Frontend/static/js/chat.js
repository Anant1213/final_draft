document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Send an initial greeting message when the page loads
    fetch('/greet')
        .then(response => response.json())
        .then(data => {
            addMessage("Bot: " + data.message, 'bot');
        });

    sendButton.addEventListener('click', () => {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage("You: " + message, 'user');

        fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addMessage("Bot: " + data.error, 'bot');
                } else if (data.message) {
                    addMessage("Bot: " + data.message, 'bot');
                }
                userInput.value = '';
            })
            .catch(error => {
                console.error('Error:', error);
                addMessage("Bot: Error communicating with the server.", 'bot');
            });
    });

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        messageDiv.textContent = text;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
