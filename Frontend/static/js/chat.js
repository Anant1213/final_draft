document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    sendButton.addEventListener('click', () => {
        const message = userInput.value.trim();

        if (!message) return;  // Don't proceed if the message is empty

        // Add the user message to the chat box
        addMessage("You: " + message, 'user');

        // Send the query to the backend
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })  // Pass only the message, backend manages the flow
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                // Handle errors and show them to the user
                addMessage("Bot: " + data.error, 'bot');
            } else if (data.message) {
                // Display the chatbot's response
                addMessage("Bot: " + data.message, 'bot');
            }

            // Clear the input field after sending the message
            userInput.value = '';  // Clear input for next message
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
