/**
 * General utility functions
 */

// Format dates consistently
function formatDate(date) {
    return new Date(date).toLocaleString();
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        return false;
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    // Implementation for toast notifications if needed
    console.log(`[${type.toUpperCase()}] ${message}`);
}