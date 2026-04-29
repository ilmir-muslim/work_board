function startTimer(taskId, button) {
    fetch(`/developers/api/timer/start/${taskId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                button.disabled = true;
            }
        });
}