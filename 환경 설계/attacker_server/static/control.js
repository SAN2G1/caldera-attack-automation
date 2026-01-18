function loadAgents() {
    fetch('/api/agents')
        .then(r => r.json())
        .then(data => {
            let html = '';
            data.agents.forEach(f => {
                html += `<div class="file-item" onclick="downloadFile('/agents/${f}', '${f}')">
                    [FILE] ${f} <span style="float:right; color:#999;">Click to download</span>
                </div>`;
            });
            document.getElementById('agentList').innerHTML = html;
        });
}

function downloadFile(url, filename) {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

function loadLogs() {
    fetch('/api/logs')
        .then(r => r.json())
        .then(data => {
            document.getElementById('logContainer').innerHTML = data.logs.join('<br>');
            document.getElementById('logContainer').style.display = 'block';
        });
}

loadAgents();