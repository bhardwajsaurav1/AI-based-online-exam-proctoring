// AI-Based Online Exam Proctoring - Neural Vision Deep Learning Engine
document.addEventListener("DOMContentLoaded", async () => {
    let timeLeft = 30 * 60; // 30 minutes
    const MAX_WARNINGS = 5;
    let warningCount = 0;
    let isDisqualified = false;

    // Calibration & Warmup Grace Period (5 seconds)
    let calibrationSeconds = 5;
    let isCalibrating = true;

    // Detection State Counters
    let faceViolationFrames = 0;
    let violationCooldown = 0;

    // AI Models
    let blazeModel = null;
    let isAIReady = false;

    // DOM Elements
    const timerElem = document.getElementById("exam-timer");
    const warnMeterDigits = document.getElementById("warn-meter-digits");
    const warnCountElem = document.getElementById("warn-count");
    const violationBanner = document.getElementById("violation-banner");
    const violationText = document.getElementById("violation-text");
    const videoContainer = document.querySelector(".video-container");
    const aiBadge = document.getElementById("ai-model-badge");

    const teleFace = document.getElementById("tele-face");
    const telePose = document.getElementById("tele-pose");
    const teleGaze = document.getElementById("tele-gaze");
    const teleMouth = document.getElementById("tele-mouth");
    const teleObject = document.getElementById("tele-object");
    const teleFocus = document.getElementById("tele-focus");
    const teleAudio = document.getElementById("tele-audio");
    const audioMeterBar = document.getElementById("audio-meter-bar");

    // Prohibited Object Detection
    let cocoModel = null;
    let detectedProhibitedObjects = [];
    let objectViolationFrames = 0;
    let visionFrameCount = 0;
    const PROHIBITED_CLASSES = ["cell phone", "phone", "mobile phone", "laptop", "book", "tv", "remote", "tablet", "mouse", "keyboard"];

    let mouthViolationFrames = 0;
    let baselineMouthRatio = 1.30;
    let calibratedMouthRatios = [];
    let currentMicVolumePct = 0;

    // Web Audio API Acoustic Surveillance
    let audioContext = null;
    let audioAnalyser = null;
    let micStream = null;
    let audioViolationFrames = 0;
    const NOISE_THRESHOLD = 0.06; // Sensitive RMS threshold for talking / background noise

    const videoElem = document.getElementById("client-video");
    const canvasElem = document.getElementById("client-canvas");
    let ctx = canvasElem ? canvasElem.getContext("2d", { willReadFrequently: true }) : null;

    const tabSwitchModal = document.getElementById("tab-switch-modal");
    const modalWarnCount = document.getElementById("modal-warn-count");
    const modalAckBtn = document.getElementById("modal-acknowledge-btn");
    const disqualifiedOverlay = document.getElementById("disqualified-overlay");
    const examPanel = document.getElementById("exam-panel");
    const examMainContainer = document.getElementById("exam-main-container");

    // Calibration Countdown Timer
    const calibInterval = setInterval(() => {
        if (calibrationSeconds > 1) {
            calibrationSeconds--;
            if (aiBadge) aiBadge.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Calibrating (${calibrationSeconds}s)`;
        } else {
            clearInterval(calibInterval);
            calibrationSeconds = 0;
            isCalibrating = false;
            if (aiBadge) {
                aiBadge.innerHTML = `<i class="fa-solid fa-check"></i> AI Active`;
                aiBadge.style.color = "#10b981";
            }
        }
    }, 1000);

    // 1. Synthesized Audio Warning Alerts
    function playWarningBeep(freq = 2800, duration = 0.35) {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = "sawtooth";
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + duration);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + duration);
        } catch (e) {}
    }

    function playDisqualifyAlarm() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = "square";
            osc.frequency.setValueAtTime(800, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(300, audioCtx.currentTime + 1.2);
            gain.gain.setValueAtTime(0.4, audioCtx.currentTime);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 1.2);
        } catch (e) {}
    }

    // 2. Countdown Timer
    const timerInterval = setInterval(() => {
        if (isDisqualified) {
            clearInterval(timerInterval);
            return;
        }
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            alert("Examination time has expired. Submitting assessment...");
            document.getElementById("exam-form").submit();
            return;
        }
        timeLeft--;
        const mins = Math.floor(timeLeft / 60);
        const secs = timeLeft % 60;
        if (timerElem) {
            timerElem.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
    }, 1000);

    // 3. Violation Handler & Disqualification Threshold
    async function triggerViolation(reason, details = "") {
        if (isDisqualified || isCalibrating) return;

        warningCount++;
        playWarningBeep();

        // Update UI counters
        if (warnMeterDigits) warnMeterDigits.textContent = `${warningCount} / ${MAX_WARNINGS}`;
        if (warnCountElem) warnCountElem.textContent = `${warningCount} / ${MAX_WARNINGS}`;
        if (modalWarnCount) modalWarnCount.textContent = `${warningCount} / ${MAX_WARNINGS}`;

        // Show banner
        if (violationBanner && violationText) {
            violationBanner.classList.remove("hidden");
            violationText.textContent = `VIOLATION: ${reason}`;
            if (videoContainer) videoContainer.classList.add("violation-active");
            setTimeout(() => {
                if (videoContainer) videoContainer.classList.remove("violation-active");
            }, 3000);
        }

        // Send to backend
        try {
            fetch("/log_violation", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ type: reason, details: details })
            });
        } catch (e) {}

        // Check Disqualification Threshold
        if (warningCount >= MAX_WARNINGS) {
            terminateAndDisqualify(reason);
        }
    }

    // 4. "Make Test Disappear" and Disqualify
    async function terminateAndDisqualify(finalReason) {
        if (isDisqualified) return;
        isDisqualified = true;

        playDisqualifyAlarm();

        // Instantly hide / remove test environment
        if (examPanel) examPanel.style.display = "none";
        if (examMainContainer) examMainContainer.style.display = "none";

        // Show full-screen disqualification overlay
        if (disqualifiedOverlay) {
            disqualifiedOverlay.classList.remove("hidden");
        }

        // Inform backend
        try {
            const res = await fetch("/disqualify_exam", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ reason: finalReason })
            });
            const data = await res.json();
            setTimeout(() => {
                window.location.href = data.redirect_url || "/results";
            }, 3000);
        } catch (e) {
            setTimeout(() => {
                window.location.href = "/results";
            }, 3000);
        }
    }

    // 5. Tab Switch & Window Focus Monitor
    let tabSwitchDebounce = false;

    function handleTabSwitch(evtName) {
        if (isDisqualified || isCalibrating || tabSwitchDebounce) return;
        tabSwitchDebounce = true;
        setTimeout(() => { tabSwitchDebounce = false; }, 2000);

        if (teleFocus) {
            teleFocus.textContent = "Unfocused / Left Tab";
            teleFocus.className = "badge-status badge-warn";
        }

        triggerViolation("Tab Switch or Window Blur Detected", evtName);

        if (!isDisqualified && tabSwitchModal) {
            tabSwitchModal.classList.remove("hidden");
        }
    }

    document.addEventListener("visibilitychange", () => {
        if (document.hidden) {
            handleTabSwitch("visibilitychange: hidden");
        } else {
            if (teleFocus) {
                teleFocus.textContent = "Active Tab";
                teleFocus.className = "badge-status badge-ok";
            }
        }
    });

    window.addEventListener("blur", () => {
        handleTabSwitch("window.onblur");
    });

    if (modalAckBtn) {
        modalAckBtn.addEventListener("click", () => {
            if (tabSwitchModal) tabSwitchModal.classList.add("hidden");
            if (teleFocus) {
                teleFocus.textContent = "Active Tab";
                teleFocus.className = "badge-status badge-ok";
            }
        });
    }

    // 6. Initialize Browser Webcam & Microphone Audio Stream
    async function startCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.warn("MediaDevices not supported on this browser.");
            return;
        }

        // 6A. Acquire Camera Video Stream
        try {
            const videoStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 } }
            });
            if (videoElem) {
                videoElem.srcObject = videoStream;
                videoElem.onloadedmetadata = () => {
                    videoElem.play();
                    if (canvasElem) {
                        canvasElem.width = videoElem.videoWidth || 640;
                        canvasElem.height = videoElem.videoHeight || 480;
                    }
                };
            }
        } catch (vErr) {
            console.warn("Camera stream access error:", vErr);
            if (teleFace) {
                teleFace.textContent = "Camera Denied";
                teleFace.className = "badge-status badge-warn";
            }
        }

        // 6B. Explicitly Acquire Microphone Stream for Acoustic Surveillance
        try {
            const audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: { echoCancellation: true, noiseSuppression: false, autoGainControl: true } 
            });
            initWebAudioMonitoring(audioStream);
        } catch (aErr) {
            console.warn("Microphone stream access error:", aErr);
            if (teleAudio) {
                teleAudio.textContent = "Mic Denied / Inactive";
                teleAudio.className = "badge-status badge-warn";
            }
        }
    }

    // 6C. Real-Time Web Audio API Acoustic Noise Surveillance
    function initWebAudioMonitoring(stream) {
        try {
            if (!stream || stream.getAudioTracks().length === 0) {
                if (teleAudio) {
                    teleAudio.textContent = "Mic Inactive";
                    teleAudio.className = "badge-status badge-warn";
                }
                return;
            }

            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            audioContext = new AudioCtx();
            audioAnalyser = audioContext.createAnalyser();
            audioAnalyser.fftSize = 256;
            audioAnalyser.smoothingTimeConstant = 0.2;

            micStream = audioContext.createMediaStreamSource(stream);
            micStream.connect(audioAnalyser);

            // Auto-resume AudioContext on first user interaction if suspended
            const unlockAudio = () => {
                if (audioContext && audioContext.state === 'suspended') {
                    audioContext.resume();
                }
            };
            document.addEventListener('click', unlockAudio, { passive: true });
            document.addEventListener('keydown', unlockAudio, { passive: true });
            document.addEventListener('focus', unlockAudio, { passive: true });

            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }

            if (teleAudio) {
                teleAudio.textContent = "Active & Quiet (0%)";
                teleAudio.className = "badge-status badge-ok";
            }

            startAudioMonitorLoop();
        } catch (e) {
            console.warn("Audio monitoring initialization error:", e);
            if (teleAudio) {
                teleAudio.textContent = "Mic Error";
                teleAudio.className = "badge-status badge-warn";
            }
        }
    }

    function startAudioMonitorLoop() {
        if (!audioAnalyser || isDisqualified) return;

        // Ensure AudioContext is running
        if (audioContext && audioContext.state === 'suspended') {
            audioContext.resume().catch(() => {});
        }

        const bufferLength = audioAnalyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        audioAnalyser.getByteTimeDomainData(dataArray);

        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            const val = (dataArray[i] - 128) / 128.0;
            sum += val * val;
        }
        const rms = Math.sqrt(sum / bufferLength);
        const volumePct = Math.min(100, Math.round(rms * 400)); // Normalized 0-100% volume
        currentMicVolumePct = volumePct;

        // Update live visual audio meter bar
        if (audioMeterBar) {
            audioMeterBar.style.width = `${Math.min(100, volumePct * 1.5)}%`;
            audioMeterBar.style.backgroundColor = (volumePct > 20) ? "#ef4444" : "#10b981";
        }

        if (!isCalibrating) {
            if (rms > NOISE_THRESHOLD || volumePct > 20) {
                audioViolationFrames++;
                if (teleAudio) {
                    teleAudio.textContent = `🚨 Talking/Noise (${volumePct}%)`;
                    teleAudio.className = "badge-status badge-warn";
                }
                // If noise/speech is sustained for ~1.0s (12 frames)
                if (audioViolationFrames > 12 && violationCooldown === 0) {
                    violationCooldown = 25;
                    triggerViolation("Acoustic Noise / Talking Detected", `Mic volume level: ${volumePct}%`);
                }
            } else {
                if (audioViolationFrames > 0) audioViolationFrames--;
                if (teleAudio && audioViolationFrames === 0) {
                    teleAudio.textContent = `Active & Quiet (${volumePct}%)`;
                    teleAudio.className = "badge-status badge-ok";
                }
            }
        }

        setTimeout(() => {
            requestAnimationFrame(startAudioMonitorLoop);
        }, 80);
    }

    await startCamera();

    // 7. Load BlazeFace & COCO-SSD Deep Learning Models
    async function loadAIModels() {
        try {
            if (typeof blazeface !== 'undefined') {
                blazeModel = await blazeface.load();
            }
            if (typeof cocoSsd !== 'undefined') {
                cocoModel = await cocoSsd.load();
            }
            isAIReady = true;
        } catch (e) {
            console.warn("AI model loading warning:", e);
        }
    }

    loadAIModels();

    // 8. Main High-Precision Face Tracking & Out-of-Frame Vision Loop
    async function proctorVisionLoop() {
        if (!ctx || !videoElem || videoElem.paused || videoElem.ended || isDisqualified) {
            requestAnimationFrame(proctorVisionLoop);
            return;
        }

        const w = canvasElem.width;
        const h = canvasElem.height;
        if (w === 0 || h === 0) {
            requestAnimationFrame(proctorVisionLoop);
            return;
        }

        ctx.clearRect(0, 0, w, h);

        const cx = w / 2;
        const cy = h / 2;
        const boxW = w * 0.52;
        const boxH = h * 0.72;
        const targetBox = {
            minX: cx - boxW / 2,
            maxX: cx + boxW / 2,
            minY: cy - boxH / 2,
            maxY: cy + boxH / 2
        };

        let faceDetected = false;
        let faceInsideBox = true;
        let faceBoxes = [];
        let headPoseState = "Forward";
        let gazeState = "Center";
        let mouthState = "Closed";

        // --- STEP A: DEEP LEARNING BLAZEFACE DETECTION ---
        if (blazeModel) {
            try {
                const predictions = await blazeModel.estimateFaces(videoElem, false);
                if (predictions && predictions.length > 0) {
                    predictions.forEach(p => {
                        const start = p.topLeft;
                        const end = p.bottomRight;
                        const fw = end[0] - start[0];
                        const fh = end[1] - start[1];
                        
                        // Mirrored coordinate calculation
                        const mirX = w - (start[0] + fw);
                        const fb = { x: mirX, y: start[1], width: fw, height: fh, landmarks: p.landmarks };
                        faceBoxes.push(fb);

                        const fcx = fb.x + fb.width / 2;
                        const fcy = fb.y + fb.height / 2;
                        if (
                            fcx < targetBox.minX || 
                            fcx > targetBox.maxX || 
                            fcy < targetBox.minY || 
                            fcy > targetBox.maxY
                        ) {
                            faceInsideBox = false;
                        }

                        // Estimate Head Pose, Gaze, and Mouth Opening from Facial Keypoints
                        // Landmarks: [rightEye, leftEye, noseTip, mouthCenter, rightEar, leftEar]
                        if (p.landmarks && p.landmarks.length >= 4) {
                            const rightEyeX = w - p.landmarks[0][0];
                            const leftEyeX = w - p.landmarks[1][0];
                            const noseX = w - p.landmarks[2][0];
                            const eyeMidX = (rightEyeX + leftEyeX) / 2;

                            const yawDiff = noseX - eyeMidX;
                            if (yawDiff > 22) {
                                headPoseState = "Looking Left";
                                gazeState = "Left";
                            } else if (yawDiff < -22) {
                                headPoseState = "Looking Right";
                                gazeState = "Right";
                            } else {
                                headPoseState = "Forward";
                                gazeState = "Center";
                            }

                            // Calculate Mouth Vertical Aspect Ratio (MAR proxy)
                            const eyeMidY = (p.landmarks[0][1] + p.landmarks[1][1]) / 2;
                            const noseY = p.landmarks[2][1];
                            const mouthY = p.landmarks[3][1];
                            const eyeToNose = Math.abs(noseY - eyeMidY);
                            const noseToMouth = Math.abs(mouthY - noseY);
                            const mouthRatio = noseToMouth / (eyeToNose || 1.0);

                            // Calibrate resting baseline mouth ratio during initial warmup
                            if (isCalibrating) {
                                if (mouthRatio > 0.5 && mouthRatio < 2.5) {
                                    calibratedMouthRatios.push(mouthRatio);
                                    if (calibratedMouthRatios.length > 5) {
                                        baselineMouthRatio = calibratedMouthRatios.reduce((a, b) => a + b, 0) / calibratedMouthRatios.length;
                                    }
                                }
                            } else {
                                // Multi-modal Speech & Mouth Tracking:
                                // 1. Substantial vertical jaw opening (>35% above calibrated resting baseline)
                                const isJawDropped = mouthRatio > Math.max(1.68, baselineMouthRatio * 1.35);
                                // 2. Vocal speech activity detected by microphone (>16% volume)
                                const isVocalizing = currentMicVolumePct > 16;

                                if (isJawDropped || isVocalizing) {
                                    mouthState = "Open";
                                }
                            }
                        }
                    });
                    faceDetected = true;
                }
            } catch (e) {}
        }

        // --- STEP A2: REAL-TIME PROHIBITED OBJECT DETECTION (COCO-SSD) ---
        visionFrameCount++;
        let foundProhibitedLabel = null;
        if (cocoModel) {
            try {
                const objPredictions = await cocoModel.detect(videoElem);
                detectedProhibitedObjects = [];

                if (objPredictions && objPredictions.length > 0) {
                    objPredictions.forEach(pred => {
                        const cName = pred.class.toLowerCase();
                        // Sensitive threshold (0.28) ensures objects anywhere in frame (corners, edges, handheld) are detected
                        if (pred.score > 0.28 && PROHIBITED_CLASSES.some(cls => cName.includes(cls))) {
                            detectedProhibitedObjects.push({
                                bbox: pred.bbox,
                                class: cName,
                                score: pred.score
                            });
                            foundProhibitedLabel = cName;
                        }
                    });
                }

                if (!isCalibrating) {
                    if (foundProhibitedLabel) {
                        objectViolationFrames++;
                        if (teleObject) {
                            teleObject.textContent = `🚨 ${foundProhibitedLabel.toUpperCase()}`;
                            teleObject.className = "badge-status badge-danger";
                        }
                        if (objectViolationFrames >= 2 && violationCooldown === 0) {
                            violationCooldown = 30;
                            triggerViolation(`Prohibited Object: ${foundProhibitedLabel.toUpperCase()}`, `Detected unauthorized ${foundProhibitedLabel} anywhere in camera view`);
                        }
                    } else {
                        if (objectViolationFrames > 0) objectViolationFrames--;
                        if (teleObject && objectViolationFrames === 0) {
                            teleObject.textContent = "Clean (No Items)";
                            teleObject.className = "badge-status badge-ok";
                        }
                    }
                }
            } catch (e) {}
        }

        // --- STEP B: DRAW TARGET HUD & CALIBRATION OVERLAYS ---
        const hasViolation = !isCalibrating && (!faceDetected || !faceInsideBox || faceBoxes.length > 1 || headPoseState !== "Forward" || mouthState === "Open" || detectedProhibitedObjects.length > 0);
        const hudColor = isCalibrating ? "#38bdf8" : (hasViolation ? "#ef4444" : "#10b981");

        // Draw Target Bounding Zone
        ctx.strokeStyle = hudColor;
        ctx.lineWidth = 2.5;
        ctx.setLineDash([8, 4]);
        ctx.strokeRect(targetBox.minX, targetBox.minY, boxW, boxH);
        ctx.setLineDash([]);

        // Target Corners
        const cornerLen = 24;
        ctx.strokeStyle = hudColor;
        ctx.lineWidth = 3.5;
        // TL
        ctx.beginPath();
        ctx.moveTo(targetBox.minX, targetBox.minY + cornerLen);
        ctx.lineTo(targetBox.minX, targetBox.minY);
        ctx.lineTo(targetBox.minX + cornerLen, targetBox.minY);
        ctx.stroke();
        // TR
        ctx.beginPath();
        ctx.moveTo(targetBox.maxX - cornerLen, targetBox.minY);
        ctx.lineTo(targetBox.maxX, targetBox.minY);
        ctx.lineTo(targetBox.maxX, targetBox.minY + cornerLen);
        ctx.stroke();
        // BL
        ctx.beginPath();
        ctx.moveTo(targetBox.minX, targetBox.maxY - cornerLen);
        ctx.lineTo(targetBox.minX, targetBox.maxY);
        ctx.lineTo(targetBox.minX + cornerLen, targetBox.maxY);
        ctx.stroke();
        // BR
        ctx.beginPath();
        ctx.moveTo(targetBox.maxX - cornerLen, targetBox.maxY);
        ctx.lineTo(targetBox.maxX, targetBox.maxY);
        ctx.lineTo(targetBox.maxX, targetBox.maxY - cornerLen);
        ctx.stroke();

        // 1. Draw Real Face Bounding Box & Facial Keypoints
        const isMultiplePersons = faceBoxes.length >= 2;
        faceBoxes.forEach((fb, idx) => {
            const isSingleCenteredFace = !isMultiplePersons && faceInsideBox && faceBoxes.length === 1 && headPoseState === "Forward";
            ctx.strokeStyle = isCalibrating ? "#38bdf8" : (isMultiplePersons ? "#ef4444" : (isSingleCenteredFace ? "#10b981" : "#f59e0b"));
            ctx.lineWidth = isMultiplePersons ? 3.5 : 2.5;
            ctx.strokeRect(fb.x, fb.y, fb.width, fb.height);

            // Label
            ctx.fillStyle = ctx.strokeStyle;
            ctx.font = "bold 12px sans-serif";
            const labelText = isCalibrating 
                ? "CALIBRATING FACE" 
                : (isMultiplePersons 
                    ? `⚠️ CONCERN: PERSON ${idx + 1} DETECTED` 
                    : (isSingleCenteredFace ? "FACE CENTERED" : "OUT OF BOUNDS"));
            ctx.fillText(labelText, fb.x + 4, fb.y - 6);

            // Draw facial keypoints (eyes, nose, mouth)
            if (fb.landmarks) {
                ctx.fillStyle = isMultiplePersons ? "#ef4444" : "#38bdf8";
                fb.landmarks.forEach(pt => {
                    const mirPtX = w - pt[0];
                    ctx.beginPath();
                    ctx.arc(mirPtX, pt[1], 3, 0, 2 * Math.PI);
                    ctx.fill();
                });
            }
        });

        // 2. Draw Detected Prohibited Object Bounding Boxes (Cell phone, Laptop, Books anywhere in frame)
        const vidW = videoElem.videoWidth || w;
        const vidH = videoElem.videoHeight || h;
        const scaleX = w / vidW;
        const scaleY = h / vidH;

        detectedProhibitedObjects.forEach(obj => {
            const ox = obj.bbox[0] * scaleX;
            const oy = obj.bbox[1] * scaleY;
            const ow = obj.bbox[2] * scaleX;
            const oh = obj.bbox[3] * scaleY;
            const mirOX = w - (ox + ow);

            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 3.5;
            ctx.strokeRect(mirOX, oy, ow, oh);

            ctx.fillStyle = "rgba(239, 68, 68, 0.92)";
            const bannerWidth = Math.max(160, ow);
            ctx.fillRect(mirOX, Math.max(0, oy - 22), bannerWidth, 22);
            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 12px sans-serif";
            ctx.fillText(`🚨 BANNED: ${obj.class.toUpperCase()} (${Math.round(obj.score * 100)}%)`, mirOX + 6, Math.max(15, oy - 6));
        });

        // Calibration Overlay Guide Banner
        if (isCalibrating) {
            ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
            ctx.fillRect(0, h - 34, w, 34);
            ctx.fillStyle = "#38bdf8";
            ctx.font = "bold 12px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(`🎥 Calibrating Camera & Face Position... (${calibrationSeconds}s)`, w / 2, h - 12);
            ctx.textAlign = "left";
        }

        // --- STEP C: EVALUATE & TRIGGER VIOLATIONS (AFTER CALIBRATION) ---
        if (!isCalibrating) {
            if (violationCooldown > 0) violationCooldown--;

            if (!faceDetected || !faceInsideBox || faceBoxes.length > 1 || headPoseState !== "Forward") {
                faceViolationFrames++;

                if (faceBoxes.length >= 2) {
                    if (teleFace) {
                        teleFace.textContent = `🚨 Concern: ${faceBoxes.length} Persons Detected`;
                        teleFace.className = "badge-status badge-danger";
                    }
                    if (telePose) {
                        telePose.textContent = "Multiple People in View";
                        telePose.className = "badge-status badge-warn";
                    }
                } else if (!faceDetected) {
                    if (teleFace) {
                        teleFace.textContent = "No Face Detected";
                        teleFace.className = "badge-status badge-warn";
                    }
                    if (telePose) {
                        telePose.textContent = "Out of View";
                        telePose.className = "badge-status badge-warn";
                    }
                } else if (!faceInsideBox) {
                    if (teleFace) {
                        teleFace.textContent = "Moved Outside Window";
                        teleFace.className = "badge-status badge-warn";
                    }
                    if (telePose) {
                        telePose.textContent = "Offset / Out of Bounds";
                        telePose.className = "badge-status badge-warn";
                    }
                } else if (headPoseState !== "Forward") {
                    if (telePose) {
                        telePose.textContent = headPoseState;
                        telePose.className = "badge-status badge-warn";
                    }
                    if (teleGaze) {
                        teleGaze.textContent = gazeState;
                        teleGaze.className = "badge-status badge-warn";
                    }
                }

                // Mouth Movement & Speech Tracking
                if (mouthState === "Open") {
                    mouthViolationFrames++;
                    if (teleMouth) {
                        teleMouth.textContent = "🚨 Mouth Open / Speaking";
                        teleMouth.className = "badge-status badge-warn";
                    }
                    if (mouthViolationFrames > 22 && violationCooldown === 0) {
                        violationCooldown = 25;
                        triggerViolation("Mouth Movement / Speech Detected", "Sustained speaking, whispering, or open mouth observed");
                    }
                } else {
                    if (mouthViolationFrames > 0) mouthViolationFrames--;
                    if (teleMouth && mouthViolationFrames === 0) {
                        teleMouth.textContent = "Closed & Normal";
                        teleMouth.className = "badge-status badge-ok";
                    }
                }

                // Trigger concern faster (5 frames ~ 400ms) for multiple persons, or 15 frames for gaze/position
                const requiredFrames = faceBoxes.length >= 2 ? 5 : 15;
                if (faceViolationFrames >= requiredFrames && violationCooldown === 0) {
                    violationCooldown = 25; // cooldown
                    const msg = faceBoxes.length >= 2
                        ? `CONCERN RAISED: Multiple Persons in Frame (${faceBoxes.length} People Present)`
                        : (!faceDetected 
                            ? "Face Absent from Camera View" 
                            : (headPoseState !== "Forward" ? `Looking Away (${headPoseState})` : "Face Moved Outside Examination Window"));
                    triggerViolation(msg, `Detected ${faceBoxes.length} faces in frame`);
                }
            } else {
                faceViolationFrames = 0;
                if (mouthState === "Open") {
                    mouthViolationFrames++;
                    if (teleMouth) {
                        teleMouth.textContent = "🚨 Mouth Open / Speaking";
                        teleMouth.className = "badge-status badge-warn";
                    }
                    if (mouthViolationFrames > 22 && violationCooldown === 0) {
                        violationCooldown = 25;
                        triggerViolation("Mouth Movement / Speech Detected", "Sustained speaking, whispering, or open mouth observed");
                    }
                } else {
                    if (mouthViolationFrames > 0) mouthViolationFrames--;
                    if (teleMouth && mouthViolationFrames === 0) {
                        teleMouth.textContent = "Closed & Normal";
                        teleMouth.className = "badge-status badge-ok";
                    }
                }
                if (teleFace) {
                    teleFace.textContent = "Centered & Verified";
                    teleFace.className = "badge-status badge-ok";
                }
                if (telePose) {
                    telePose.textContent = "Forward";
                    telePose.className = "badge-status badge-ok";
                }
                if (teleGaze) {
                    teleGaze.textContent = "Center";
                    teleGaze.className = "badge-status badge-ok";
                }
            }

            // Clear violation banner if clean
            if (!hasViolation && tabSwitchModal && tabSwitchModal.classList.contains("hidden") && violationBanner) {
                violationBanner.classList.add("hidden");
            }
        }

        setTimeout(() => {
            requestAnimationFrame(proctorVisionLoop);
        }, 80);
    }

    requestAnimationFrame(proctorVisionLoop);
});
