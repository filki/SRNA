// Function to search for a game title and update suggestions dynamically
async function searchGameTitle(title) {
    const suggestions = document.getElementById('game_suggestions');
    suggestions.innerHTML = ''; // Clear previous suggestions

    if (title.length < 3) return; // Only proceed if title has 3+ characters

    try {
        // Fetch matching games from the Flask endpoint
        const response = await fetch(`/search_game_title?title=${encodeURIComponent(title)}`);
        const games = await response.json();

        // Dynamically create and display suggestions
        games.forEach(game => {
            const option = document.createElement('div');
            option.classList.add('suggestion');
            option.innerHTML = `${game.name} (App ID: ${game.app_id})`;
            option.onclick = () => {
                document.getElementById('app_id').value = game.app_id; // Set App ID
                suggestions.innerHTML = ''; // Clear suggestions
            };
            suggestions.appendChild(option);
        });
    } catch (error) {
        console.error("Error fetching game titles:", error);
    }
}
