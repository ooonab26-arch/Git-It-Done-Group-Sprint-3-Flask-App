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
                            <div class="event-title"><strong>${eventData.title}</strong></div>
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
    });