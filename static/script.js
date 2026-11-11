// Copyright (c) 2026 Quietcore
// Helper to ensure we always work with strings
function ensureString(val) {
    return String(val).trim();
}

async function addUser() {
    const input = document.getElementById("user-id-input");
    let userId = ensureString(input.value);
    
    if (!userId || userId.length < 15) {
        alert("Please enter a valid Discord User ID (17-18 digits).");
        return;
    }

    const res = await fetch("/api/add_user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }) // Send as string
    });

    const data = await res.json();
    if (res.ok) {
        alert(data.message);
        input.value = ""; // Clear input
        location.reload();
    } else {
        alert("Error: " + data.message);
    }
}

async function removeUser(userId) {
    // Force string conversion immediately
    const userIdStr = ensureString(userId);
    
    if (!confirm(`Unblock user ${userIdStr}?`)) return;

    const res = await fetch("/api/remove_user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userIdStr }) // Send as string
    });

    const data = await res.json();
    if (res.ok) {
        alert(data.message);
        location.reload();
    } else {
        alert("Error: " + data.message);
    }
}

async function toggleBot() {
    const currentStatus = document.getElementById("bot-status").innerText === "Active";
    const res = await fetch("/api/toggle_bot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: !currentStatus })
    });

    const data = await res.json();
    if (res.ok) {
        alert(data.message);
        location.reload();
    } else {
        alert("Error toggling bot.");
    }
}