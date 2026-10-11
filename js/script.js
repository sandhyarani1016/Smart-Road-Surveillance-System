```javascript`
function previewFile(inputId, previewId, messageId) {
    const input = document.getElementById(inputId);
    const file = input.files[0];
    const message = document.getElementById(messageId);

    if (!file) {
        message.textContent = "Please choose a video first.";
        return;
    }

    if (!file.type.startsWith("video/")) {
        message.textContent = "Please select a valid video file.";
        input.value = "";
        return;
    }

    const url = URL.createObjectURL(file);
    message.textContent = "Selected: " + file.name;

    const video = document.getElementById(previewId);

    if (video && video.tagName === "VIDEO") {
        video.src = url;
        video.style.display = "block";
        video.load();
    }
}

// Car Counting: show selected video preview
document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("trafficFile");
    const preview = document.getElementById("trafficPreview");
    const message = document.getElementById("trafficMessage");
    const form = input ? input.closest("form") : null;
    const button = form ? form.querySelector('button[type="submit"]') : null;

    if (input && preview && message) {
        input.addEventListener("change", function () {
            if (input.files.length > 0) {
                previewFile(
                    "trafficFile",
                    "trafficPreview",
                    "trafficMessage"
                );
            } else {
                preview.removeAttribute("src");
                preview.style.display = "none";
                message.textContent = "";
            }
        });
    }

    // Submit the video to Flask for vehicle counting
    if (form) {
        form.addEventListener("submit", function (event) {
            if (!input || !input.files.length) {
                event.preventDefault();
                message.textContent = "Please choose a video first.";
                return;
            }

            if (button) {
                button.disabled = true;
                button.textContent = "Analyzing Video...";
            }
        });
    }
});

