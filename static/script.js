async function loadRandomImage() {
    const response = await fetch('/api/random?count=1');
    if (!response.ok) {
        console.error('Failed to fetch image');
        return;
    }
    let data = await response.json();
    data=data[0]
    document.getElementById('photo-fix').src = data.url;
    if (data.url_raw) document.getElementById('photo-raw').src = data.url_raw;
    else document.getElementById('photo-raw').src = '#"'
    populateTable(data);
    window.location.hash = `#${data.id}`;
}

document.getElementById('tag-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    // Placeholder for submitting tags
    await loadRandomImage();
});

window.addEventListener('load', loadRandomImage);

function populateTable(data) {
 // build a small HTML table of metadata
 const md = document.getElementById('metadata');
 md.innerHTML = `
   <table class="table table-sm table-borderless mb-0">
     <tbody>
       <tr><th scope="row">ID</th><td>${data.id}</td></tr>
       <tr><th scope="row">Sequence #</th><td>${data.fotoladu_id}</td></tr>
       <tr><th scope="row">Year</th><td>${data.aasta}</td></tr>
       <tr><th scope="row">Dimensions</th><td>${data.w} × ${data.h}</td></tr>
       <tr><th scope="row">Directory</th><td>${data.peakaust}/${data.kaust}</td></tr>
       <tr><th scope="row">Filename</th><td>${data.fail}</td></tr>
       <tr><th scope="row">Flight #</th><td>${data.lend}</td></tr>
       <tr><th scope="row">Photo #</th><td>${data.fotonr}</td></tr>
       <tr><th scope="row">Map sheet</th><td>${data.kaardileht}</td></tr>
       <tr><th scope="row">Type</th><td>${data.tyyp}</td></tr>
       <tr><th scope="row">Source</th><td>${data.allikas}</td></tr>
       <tr><th scope="row">Thumb URL</th>
           <td><a href="${data.url_thumb}" target="_blank">${data.url_thumb}</a></td>
       </tr>
     </tbody>
   </table>
 `;

}