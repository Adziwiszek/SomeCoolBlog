const form = document.getElementById('updateForm');
form.addEventListener('submit', async (event) => {
    event.preventDefault();


    const formData = new FormData(event.target);
    const response = await fetch(event.target.action, {
      method: 'PATCH',
      body: formData
    });

    if (response.ok) {
      // Redirect or display a success message
      window.location.href = '/';
    } else {
      // Handle the error
      console.error('Error updating post:', await response.text());
    }
});
