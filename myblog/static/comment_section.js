document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('message-form');
    const userMessageInput = document.getElementById('user-message');
    const chatMessages = document.getElementById('chat-messages');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });

    function sendMessage() {
        const userMessage = userMessageInput.value.trim();
        if (!userMessage) return;
        const postID = form.getAttribute('data-post-id')

        fetch('/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'X-CSRFToken': getCookie('csrf_token')  // Add this line for CSRF protection
            },
            body: JSON.stringify({
                message: userMessage,
                postID: postID
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (data.status === 'success') {
                // Add the message to the chat
                // const messageElement = document.createElement('div');
                // messageElement.textContent = userMessage;
                // chatMessages.appendChild(messageElement);
                
                // Clear the input field
                userMessageInput.value = '';
            }
        })
        .catch(error => console.error('Error:', error));
    }

    function addCommentToChat(comment) {
        const commentElement = document.createElement('div');
        commentElement.className = 'comment';
        commentElement.innerHTML = `
            <p class="comment-body">${escapeHTML(comment.body)}</p>
            <p class="comment-meta">Posted by ${escapeHTML(comment.username)} on ${comment.created}</p>
        `;
        chatMessages.appendChild(commentElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        // setInterval()
    }

    function refreshComments() {
        const postID = form.getAttribute('data-post-id');
        fetch('/'+postID+'/receive', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                // message: 'Placeholder message'  // Send a placeholder message for demonstration purposes
            })
        })
        .then(response => response.json())
        .then(data => {
            // Display the received message in the chat-box
            chatMessages.innerHTML = '';
            chatMessagesData = data['comments'];
            chatMessagesData.forEach(comment => {
                chatMessages.innerHTML +=  `<div class="comment">
                <p class="comment-body">${escapeHTML(comment.body)}</p>
                <p class="comment-meta">Posted by ${escapeHTML(comment.username)} on ${comment.created}</p>
                </div>
            `;
            });
            // chatMessages.innerHTML += `<p>${data.message}</p>`;
        }).catch(error => console.error('Error refreshing comments:', error));
    }
    refreshComments();
    setInterval(refreshComments, 5000);

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    // Function to get CSRF token from cookies
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
});