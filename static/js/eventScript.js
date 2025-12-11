document.addEventListener("DOMContentLoaded", () => { 
    document.querySelectorAll('.delete-btn').forEach(btn => { 
        btn.addEventListener('click', (e) => { 
            e.stopPropagation();
            const id = btn.dataset.id; 
            
            fetch(`/api/v1/events/${id}`, {method: 'DELETE'}) 
                .then(response => { 
                    if (response.ok){ 
                        document.getElementById(`event-${id}`).remove(); 
                    } 
                }); 
            }); 
        }); 
        document.querySelectorAll('.edit-btn').forEach (button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();

                const eventId = button.dataset.id;

                const res = await fetch(`/api/v1/events/${eventId}`);
                const data = await res.json();

                
                const modalTitle = document.querySelector("#addEventModal .modal-title");
                const submitBtn = document.querySelector("#editEventForm button[type='submit']");

                modalTitle.textContent = "Edit Event"
                submitBtn.textContent = "Save Changes"

                document.getElementById("edit-event-id").value = eventId;
                document.getElementById("edit-title").value = data.title;
                document.getElementById("edit-date").value = data.date;
                document.getElementById("edit-location").value = data.location;
                document.getElementById("edit-attendance").value = data.attendance;
                document.getElementById("edit-description").value = data.description;
                document.getElementById("edit-event-type").value = data.type_id;
                document.getElementById("edit-organizer").value = data.lead_organizer;

                document.getElementById("editEventForm").action = `/api/v1/events/${eventId}`;
            
                const modal = new bootstrap.Modal(document.getElementById('addEventModal'));
                modal.show();

            });
        });
        
        document.querySelector('[data-bs-target="#addEventModal"]').addEventListener('click', () => {
            const modalTitle = document.querySelector("#addEventModal .modal-title");
            const submitBtn = document.querySelector("#editEventForm button[type='submit']");
            modalTitle.textContent = "Add New Event";
            submitBtn.textContent = "Add Event";

            document.getElementById("edit-event-id").value = "";
            document.getElementById("edit-title").value = "";
            document.getElementById("edit-date").value = "";
            document.getElementById("edit-location").value = "";
            document.getElementById("edit-description").value = "";
            document.getElementById("edit-attendance").value = "";
            document.getElementById("edit-event-type").value = "";
            document.getElementById("edit-organizer").value = "";

            document.getElementById("editEventForm").action = "/api/v1/add_event";
        });

        
        const popupWindow = document.createElement("div"); 
        popupWindow.className = "event-card-popup"; 
        document.body.appendChild(popupWindow); 
        
        let currentVisible = false;

        document.querySelectorAll(".event-info").forEach(row => {
            row.addEventListener("click", (e) => { 
                e.stopPropagation(); 

                const eventData = JSON.parse(row.dataset.event); 

                console.log("Clicked event data:", eventData); 

                popupWindow.innerHTML = 
                    `<img src="${eventData.poster}" alt="${eventData.title}">
                     <div><strong>${eventData.title}</strong></div>

                    <div class="event-card-text">
                            <div><span class = "popup-text">Date:</span> ${eventData.date}</div>
                            <div><span class = "popup-text">Location:</span> ${eventData.location}</div>
                            <div><span class = "popup-text">Attendance:</span> ${eventData.attendance}</div>
                            <div><span class = "popup-text">Lead organizer:</span> ${eventData.lead_organizer}</div>
                            <div><span class = "popup-text">Collaborators:</span> ${eventData.partners}</div>
                    </div>

                    <div class="social-share-container">
                        <a class="linkedin" target="_blank">
                         <i class="fa fa-linkedin-square"></i> 
                        </a>
                        
                        <a class="gmail" target="_blank">
                            <i class="fa fa-google"></i> 
                        </a> 
                        
                        <a class="copy-link" target="_blank">
                            <i class="fa fa-link"></i>
                        </a>
                        
                        <a class="download" target="_blank">
                            <i class="fa fa-download"></i> 
                        </a> <a class="calendar" target="_blank"> 
                            <i class="fa fa-calendar"></i> 
                        </a> </div>` ; 
                        
                const eventURL = "https://www.colby.edu/now/"; 
                const eventTitle = encodeURIComponent(eventData.title); 

                const linkedInBtn = popupWindow.querySelector(".linkedin"); 
                linkedInBtn.href = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(eventURL)}`;
                linkedInBtn.target = "_blank";

                popupWindow.querySelector(".gmail").href = `https://mail.google.com/mail/?view=cm&fs=1&to=&su=${eventTitle}&body=${encodeURIComponent(eventURL)}`;
                popupWindow.querySelector(".calendar").href = `https://calendar.google.com/calendar/r/eventedit?text=${eventTitle}&dates=20251206T090000Z/20251206T100000Z&details=${encodeURIComponent(eventURL)}&sf=true&output=xml`;
                
                popupWindow.querySelector(".social-share-container")
                    .addEventListener('click', e => e.stopPropagation());
                
                popupWindow.querySelectorAll(".social-share-container a")
                    .forEach( btn => 
                        btn.addEventListener("click", e => 
                            e.stopPropagation()
                        )
                    );

                popupWindow.classList.add("show"); 
                currentVisible = true;
            });
        });

        
        popupWindow.addEventListener("click", e => 
            e.stopPropagation()
        );
        
        document.addEventListener("click", (e) => { 
            if (currentVisible && !e.target.closest(".event-info") && !e.target.closest(".event-card-popup")){ 
                popupWindow.classList.remove("show");
                currentVisible = false; 
            } 
        }); 

        // --- Filter events by category ---
        document.querySelectorAll('.category-card').forEach(card => {
            card.addEventListener('click', () => {
                const selectedCategory = card.dataset.category;

                // Update table title
                const tableTitle = document.getElementById('events-table-header');
                tableTitle.textContent = selectedCategory ? `${selectedCategory} Events` : "All Events";

                // Filter rows
                document.querySelectorAll('tbody tr.event-info').forEach(row => {
                    const rowData = JSON.parse(row.dataset.event);
                    if (rowData.type === selectedCategory || selectedCategory === "") {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            });
        });


});