async function loadRandomImage() {
    const response = await fetch('/api/random');
    if (!response.ok) {
        console.error('Failed to fetch image');
        return;
    }
    const data = await response.json();
    document.getElementById('photo').src = data.url;
    window.location.hash = `#${data.id}`;
}

document.getElementById('tag-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    // Placeholder for submitting tags
    await loadRandomImage();
});

window.addEventListener('load', loadRandomImage);
