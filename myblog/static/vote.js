document.addEventListener('DOMContentLoaded', function() {
    const upvoteDivs = document.querySelectorAll('[id=upvote]');
    const downvoteDivs = document.querySelectorAll('[id=downvote]');
    
    function vote(post_id, action) {
        fetch('/'+post_id+'/'+(action == 1? '/upvote' : '/downvote'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // 'X-CSRFToken': getCookie('csrf_token')  // Add this line for CSRF protection
            },
            body: JSON.stringify({
                postID: post_id
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const voteDiv = document.querySelector(`[id=${action === 1 ? 'upvote' : 'downvote'}][data-post-id="${post_id}"]`);
                if(voteDiv) {
                    voteDiv.textContent = textContent = `${action === 1 ? '↑' : '↓'} ${data.votes}`;
                }
            }
        })
        .catch(error => console.error('Error:', error));
    }

    if(upvoteDivs) {
        for(let i = 0; i < upvoteDivs.length; i++) {
            upvoteDivs[i].addEventListener('click', function()  {
                const post_id = this.getAttribute('data-post-id');
                vote(post_id, 1);
            })
        }
    }
    if(downvoteDivs) {
        for(let i = 0; i < downvoteDivs.length; i++) {
            downvoteDivs[i].addEventListener('click', function() {
                const post_id = this.getAttribute('data-post-id');
                vote(post_id, 0);
            });
        }
    }
})