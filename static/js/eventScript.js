document.addEventListener("DOMContentLoaded", () => {
    
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {

        const id = btn.dataset.id;

        fetch(`/api/v1/events/${id}`, {method: 'DELETE'})
            .then(response => {
                if (response.ok){
                    document.getElementById(`event-${id}`).remove();

                }
            });

        });
    });

});
