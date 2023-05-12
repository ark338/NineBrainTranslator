const socket = io();
const userId = Date.now();

socket.on('translation_progress', function(progress) {
    // 这是一个很差劲的实现用来区分多用户的进度显示，但是由于用户并不多且是一个demo，于是就将就了
    if (parseInt(progress.user_id) !== userId) {
        return;
    }
    const translationProgress = document.getElementById('translationProgress');
    translationProgress.textContent = progress.progress;
});

socket.on('file_progress', function(progress) {
    // 这是一个很差劲的实现用来区分多用户的进度显示，但是由于用户并不多且是一个demo，于是就将就了
    if (parseInt(progress.user_id) !== userId) {
        return;
    }
    const fileProgress = document.getElementById('fileProgress');
    fileProgress.textContent = progress.progress + '\n';
});

async function translateText() {
    const languages = getSelectedLanguages();
    if (languages.length === 0) {
        alert('Please select at least one language.');
        return;
    }

    const enableGPT4 = document.getElementById('enableGPT4').checked;
    const submitTextButton = document.getElementById('submitText');
    const inputText = document.getElementById('inputText').value;

    // 禁用按钮
    submitTextButton.disabled = true;

    const response = await fetch('/translate/text', {
        method: 'POST',
        body: new URLSearchParams({text: inputText, languages: JSON.stringify(languages), user_id: userId, enable_gpt4: enableGPT4}),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    });

    if (response.ok) {
        const translations = await response.json();
        const outputText = document.getElementById('outputText');
        outputText.value = '';
        for (const lang in translations) {
            outputText.value += `${lang}: ${translations[lang]}\n`;
        }
    } else {
        alert('Error: Translation failed.');
    }

    // 启用按钮
    submitTextButton.disabled = false;
}

async function uploadFile() {
    const languages = getSelectedLanguages();
    if (languages.length === 0) {
        alert('Please select at least one language.');
        return;
    }
    const enableGPT4 = document.getElementById('enableGPT4').checked;
    const fileInput = document.getElementById('fileInput');
    const submitFile = document.getElementById('submitFile');
    const downloadButton = document.getElementById('downloadFile');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('languages', JSON.stringify(languages));
    formData.append('user_id', userId);
    formData.append('enable_gpt4', enableGPT4);

    fileInput.disabled = true;
    submitFile.disabled = true;
    downloadButton.disabled = true;

    const response = await fetch('/translate/upload', {
        method: 'POST',
        body: formData,
    });

    if (response.ok) {
        const data = await response.json();
        fileInput.disabled = false;
        submitFile.disabled = false;
        downloadButton.disabled = false;
        downloadButton.setAttribute('data-filename', data.filename);
        alert('Translation finished');
    } else {
        fileInput.disabled = false;
        submitFile.disabled = false;
        alert('Error: File upload or Translation failed');
    }
}

function downloadTranslatedFile() {
    const downloadButton = document.getElementById('downloadFile');
    const filename = downloadButton.getAttribute('data-filename');
    window.location.href = `/translate/download/${filename}`;
}

function showTranslatingMessage() {
    const submitTextButton = document.getElementById('submitText');
    if (submitTextButton.disabled) {
        alert('Translating, please wait...');
    }
}

function getSelectedLanguages() {
    const checkboxes = document.querySelectorAll('#languages input[type="checkbox"]:checked');
    const languages = Array.from(checkboxes).map(checkbox => checkbox.value);
    return languages;
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('submitText').addEventListener('click', showTranslatingMessage);
    document.getElementById('submitText').addEventListener('click', translateText);
    document.getElementById('submitFile').addEventListener('click', uploadFile);
    document.getElementById('downloadFile').addEventListener('click', downloadTranslatedFile);
});
