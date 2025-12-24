// Listen for messages from the Popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "ask_server") {
        handleServerRequest(request.payload);
    }
});

async function handleServerRequest(payload) {
    try {
        // 1. Tell storage we are loading
        await chrome.storage.local.set({ 
            status: "loading", 
            query: payload.query 
        });

        // 2. Call the Python Backend
        const response = await fetch('http://localhost:8000/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url: payload.url, 
                query: payload.query 
            })
        });

        const data = await response.json();

        // 3. Save the result to storage
        if (data.answer) {
            await chrome.storage.local.set({ 
                status: "complete", 
                answer: data.answer 
            });
        } else {
            await chrome.storage.local.set({ 
                status: "error", 
                error: data.detail || "Unknown error" 
            });
        }

    } catch (error) {
        // Handle connection errors (e.g., server not running)
        await chrome.storage.local.set({ 
            status: "error", 
            error: "Could not connect to Python backend." 
        });
    }
}