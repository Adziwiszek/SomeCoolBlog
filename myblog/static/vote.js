document.addEventListener('DOMContentLoaded', function() {
    const upvoteDivs = document.querySelectorAll('[id=upvote]');
    const downvoteDivs = document.querySelectorAll('[id=downvote]');
    
    function vote(post_id, action) {
        fetch('/'+post_id+'/'+(action == 1 ? '/upvote' : '/downvote'), {
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
                const upvoteDiv = document.querySelector(`[id=${'upvote'}][data-post-id="${post_id}"]`);
                const downvoteDiv = document.querySelector(`[id=${'downvote'}][data-post-id="${post_id}"]`);
                if(upvoteDiv) {
                    upvoteDiv.textContent = textContent = `${'↑'} ${data.votes.upvotes}`;
                }
                if(downvoteDiv) {
                    downvoteDiv.textContent = textContent = `${'↓'} ${data.votes.downvotes}`;
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