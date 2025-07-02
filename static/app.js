async function fetchEvents() {
    try {
        const res = await fetch('/events');
        const data = await res.json();
        const container = document.getElementById('events-list');
        container.innerHTML = '';

        if (data.length === 0) {
            container.innerHTML = '<p>No events yet.</p>';
            return;
        }

        data.forEach(event => {
            const div = document.createElement('div');
            div.className = 'event';

            // Use the 'message' if MERGE, else default simple message
            if (event.action === "MERGE" && event.message) {
                div.textContent = event.message;
            } else {
                div.textContent = `"${event.author}" did ${event.action} on branch "${event.from_branch}" at ${event.timestamp}`;
            }

            container.appendChild(div);
        });

    } catch (err) {
        console.error('Failed to fetch events:', err);
    }
}

// Initial load + every 15s
fetchEvents();
setInterval(fetchEvents, 15000);
