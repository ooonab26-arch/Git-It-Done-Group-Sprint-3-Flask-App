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




    const popupWindow = document.createElement("div");
    popupWindow.className = "event-card-popup";

    document.body.appendChild(popupWindow);

    let currentVisible = false;
    document.querySelectorAll(".event-row").forEach(row => {
        row.addEventListener("click", (e) => {
            e.stopPropagation();


            const eventData = JSON.parse(row.dataset.event);

            console.log("Clicked event data:", eventData);

            popupWindow.innerHTML = `<img src="${eventData.poster}" alt="${eventData.title}">
                <div class="card-body">
                    <strong>${eventData.title}</strong>
                </div>`;

            popupWindow.classList.add("show");
            currentVisible = true;
            
        
    });

});

    document.addEventListener("click", (e) => {
        if (currentVisible && !e.target.closest(".event-row") && !e.target.closest(".event-card-popup")){
                    popupWindow.classList.remove("show");
                    currentVisible = false;


        }


    });
});
