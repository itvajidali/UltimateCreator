document.addEventListener('DOMContentLoaded', () => {
    const createBtn = document.getElementById('create-btn');
    const promptInput = document.getElementById('prompt');
    const durationInput = document.getElementById('duration');
    const voiceInput = document.getElementById('voiceId');

    const creationForm = document.querySelector('.creation-form');
    const processingState = document.getElementById('processing-state');
    const resultArea = document.getElementById('result-area');

    const statusText = document.getElementById('status-text');
    const progressBar = document.getElementById('progress-bar');
    const downloadBtn = document.getElementById('download-btn');

    createBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) {
            alert('Please enter a prompt!');
            return;
        }

        // Switch to processing UI
        creationForm.classList.add('hidden');
        processingState.classList.remove('hidden');

        try {
            // Start Job
            const response = await fetch('/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    duration: durationInput.value,
                    voice_id: voiceInput.value,
                    orientation: document.getElementById('orientation').value,
                    mood: document.getElementById('mood').value
                })
            });

            const data = await response.json();
            const jobId = data.job_id;

            // Poll Status
            pollStatus(jobId);

        } catch (error) {
            console.error(error);
            alert('Failed to start creation.');
            resetUI();
        }
    });

    async function pollStatus(jobId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/status/${jobId}`);
                const job = await res.json();

                // Update Progress
                progressBar.style.width = `${job.progress}%`;

                if (job.status === 'generating_script') statusText.innerText = "Writing Script...";
                if (job.status === 'fetching_images') statusText.innerText = "Finding Perfect Images...";
                if (job.status === 'generating_audio') statusText.innerText = "Recording Voiceover...";
                if (job.status === 'rendering_video') statusText.innerText = "Assembling Video...";

                if (job.status === 'completed') {
                    clearInterval(interval);
                    showResult(jobId, job);
                } else if (job.status === 'failed') {
                    clearInterval(interval);
                    alert(`Error: ${job.error}`);
                    resetUI();
                }

            } catch (e) {
                console.error("Polling error", e);
            }
        }, 1000); // Check every 1s
    }

    function showResult(jobId, jobData) {
        processingState.classList.add('hidden');
        resultArea.classList.remove('hidden');

        downloadBtn.href = `/download/${jobId}`;

        // Thumbnail Button
        const thumbBtn = document.getElementById('download-thumb-btn');
        if (thumbBtn) {
            thumbBtn.href = `/download/thumbnail/${jobId}`;
            thumbBtn.style.display = 'inline-flex';
        }

        // Dubbing Button (Check if Hindi dub exists)
        const dubBtn = document.getElementById('download-dub-btn');
        if (dubBtn && jobData.dubbed_versions && jobData.dubbed_versions.length > 0) {
            dubBtn.href = `/download/dub/${jobId}/Hindi`;
            dubBtn.style.display = 'inline-flex';
            dubBtn.innerHTML = `<i class="fa-solid fa-language"></i> Download Hindi Dub`;
        }
    }

    function resetUI() {
        creationForm.classList.remove('hidden');
        processingState.classList.add('hidden');
        resultArea.classList.add('hidden');
        progressBar.style.width = '0%';
        statusText.innerText = 'Initializing...';
    }
});
