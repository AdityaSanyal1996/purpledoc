document.addEventListener('DOMContentLoaded', async () => {
    const chat = document.getElementById('chat');
    const statusDiv = document.createElement('div'); 
    statusDiv.id = "status-indicator";
    chat.parentNode.insertBefore(statusDiv, chat);

    // 1. Restore previous state from Storage (Runs when you open popup)
    const data = await chrome.storage.local.get(["status", "query", "answer", "error"]);
    
    if (data.status === "loading") {
        chat.innerHTML = `<div class="user"><strong>You:</strong> ${data.query}</div>`;
        statusDiv.innerText = "Thinking... (You can switch tabs)";
        statusDiv.style.color = "orange";
    } else if (data.status === "complete") {
        chat.innerHTML = `<div class="user"><strong>You:</strong> ${data.query}</div>`;
        chat.innerHTML += `<div class="ai"><strong>AI:</strong> ${data.answer}</div>`;
        statusDiv.innerText = "";
    } else if (data.status === "error") {
        chat.innerHTML = `<div class="error">${data.error}</div>`;
    }

    // 2. Listen for "Real-time" updates from Background
    chrome.storage.onChanged.addListener((changes, namespace) => {
        if (changes.status) {
            const newStatus = changes.status.newValue;
            if (newStatus === "loading") {
                statusDiv.innerText = "Thinking... (You can switch tabs)";
                statusDiv.style.color = "orange";
            } else if (newStatus === "complete") {
                statusDiv.innerText = "";
                // Only append if not already there to avoid duplicates
                if (!chat.innerHTML.includes(changes.answer.newValue)) {
                    chrome.storage.local.get("query", (d) => {
                         if(!chat.innerHTML.includes(d.query)) 
                            chat.innerHTML += `<div class="user"><strong>You:</strong> ${d.query}</div>`;
                         chat.innerHTML += `<div class="ai"><strong>AI:</strong> ${changes.answer.newValue}</div>`;
                    });
                }
            } else if (newStatus === "error") {
                statusDiv.innerText = "Error";
                statusDiv.style.color = "red";
            }
        }
    });

    // 3. Handle the "Ask" button
    document.getElementById('ask').addEventListener('click', async () => {
        const query = document.getElementById('query').value;
        if (!query) return;

        // Reset UI
        chat.innerHTML = `<div class="user"><strong>You:</strong> ${query}</div>`;
        document.getElementById('query').value = "";
        
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        // Send message to Background Worker
        chrome.runtime.sendMessage({ 
            action: "ask_server", 
            payload: { url: tab.url, query: query } 
        });
    });
});