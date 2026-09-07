// Live Exam Proctoring Telemetry Poller & Timer
document.addEventListener("DOMContentLoaded", () => {
    let timeLeft = 30 * 60; // 30 minutes in seconds
    const timerElem = document.getElementById("exam-timer");
    const violationBanner = document.getElementById("violation-banner");
    const violationText = document.getElementById("violation-text");

    // Elements for Diagnostics HUD
    const teleFace = document.getElementById("tele-face");
    const teleGaze = document.getElementById("tele-gaze");
    const teleBlink = document.getElementById("tele-blink");
    const telePose = document.getElementById("tele-pose");
    const teleMouth = document.getElementById("tele-mouth");
    const teleObj = document.getElementById("tele-obj");
    const teleAudio = document.getElementById("tele-audio");
    const warnCountElem = document.getElementById("warn-count");

    // Synthesized Web Audio Beep fallback for browsers
    function playWarningBeep() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = "sine";
            osc.frequency.setValueAtTime(2500, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.4);
        } catch (e) {
            // Audio context not allowed until user interaction
        }
    }

    // Countdown Timer
    const timerInterval = setInterval(() => {
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            alert("Examination time has expired. Submitting your assessment...");
            document.getElementById("exam-form").submit();
            return;
        }
        timeLeft--;
        const mins = Math.floor(timeLeft / 60);
        const secs = timeLeft % 60;
        timerElem.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }, 1000);

    let lastWarnCount = 0;

    // Real-Time Telemetry Polling (Every 600ms)
    async function pollTelemetry() {
        try {
            const res = await fetch("/telemetry");
            if (!res.ok) return;
            const data = await res.json();

            // 1. Update Face Presence
            teleFace.textContent = data.face_status || "Normal";
            teleFace.className = data.face_count === 1 ? "badge-status badge-ok" : "badge-status badge-warn";

            // 2. Eye Gaze
            teleGaze.textContent = (data.gaze_direction || "center").toUpperCase();
            teleGaze.className = data.gaze_direction === "center" ? "badge-status badge-ok" : "badge-status badge-warn";

            // 3. Blink / Liveness
            teleBlink.textContent = data.blink_status || "Active";

            // 4. Head Orientation
            telePose.textContent = data.head_looking_away ? "Looking Away" : "Forward";
            telePose.className = !data.head_looking_away ? "badge-status badge-ok" : "badge-status badge-warn";

            // 5. Mouth Status
            teleMouth.textContent = data.mouth_status || "Mouth Close";
            teleMouth.className = data.mouth_status === "Mouth Close" ? "badge-status badge-ok" : "badge-status badge-warn";

            // 6. Object Detection
            const objs = data.detected_objects || [];
            const nonPersonObjs = objs.filter(o => o[0] !== "person").map(o => o[0]);
            if (nonPersonObjs.length > 0) {
                teleObj.textContent = nonPersonObjs.join(", ");
                teleObj.className = "badge-status badge-warn";
            } else {
                teleObj.textContent = "None";
                teleObj.className = "badge-status badge-ok";
            }

            // 7. Audio Status
            teleAudio.textContent = data.audio_status || "Quiet";
            teleAudio.className = data.audio_status.includes("Suspicious") ? "badge-status badge-warn" : "badge-status badge-ok";

            // 8. Warning Counter
            if (data.warning_count !== undefined) {
                warnCountElem.textContent = data.warning_count;
                if (data.warning_count > lastWarnCount) {
                    playWarningBeep();
                    lastWarnCount = data.warning_count;
                }
            }

            // 9. Violation Banner Display
            if (data.is_violation) {
                violationBanner.classList.remove("hidden");
                let reasons = [];
                if (data.face_count === 0) reasons.push("Face Missing");
                if (data.face_count > 1) reasons.push("Multiple Faces");
                if (data.head_looking_away) reasons.push("Look at Screen");
                if (nonPersonObjs.length > 0) reasons.push(`Unauthorized: ${nonPersonObjs[0]}`);
                if (data.audio_status.includes("Suspicious")) reasons.push("Noise Detected");
                violationText.textContent = `Warning: ${reasons.join(" | ") || "Anomaly Detected"}`;
            } else {
                violationBanner.classList.add("hidden");
            }

        } catch (err) {
            console.error("Telemetry poll failed:", err);
        }
    }

    setInterval(pollTelemetry, 600);
});
