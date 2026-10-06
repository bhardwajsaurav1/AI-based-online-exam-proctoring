"""
Dynamic AI & Adaptive Exam Question Bank.
Author: Sole Contributor / Creator
Provides a comprehensive bank of computer science, AI, OS, and software engineering questions.
Generates randomized problem sets for every candidate session via Gemini AI, Open-Source Live Feed, or Local Bank.
"""

import os
import json
import html
import random
import requests
import config


QUESTION_BANK = [
    {
        "id": "q_os_01",
        "category": "Operating Systems",
        "question": "What is the primary function of the Operating System Kernel?",
        "options": [
            {"key": "A", "text": "Compiling high-level programming source code"},
            {"key": "B", "text": "Managing hardware resources and mediating between software and CPU"},
            {"key": "C", "text": "Rendering 3D computer graphics on the monitor"},
            {"key": "D", "text": "Encrypting network traffic across the internet"}
        ],
        "correct": "B"
    },
    {
        "id": "q_arch_01",
        "category": "Computer Architecture",
        "question": "Which memory hierarchy level provides the fastest data access speed?",
        "options": [
            {"key": "A", "text": "CPU Registers"},
            {"key": "B", "text": "L1 Cache"},
            {"key": "C", "text": "Main Memory (RAM)"},
            {"key": "D", "text": "Solid State Drive (NVMe SSD)"}
        ],
        "correct": "A"
    },
    {
        "id": "q_cv_01",
        "category": "Computer Vision & AI",
        "question": "In Computer Vision, what is the purpose of the Perspective-n-Point (PnP) algorithm?",
        "options": [
            {"key": "A", "text": "Image compression and JPEG encoding"},
            {"key": "B", "text": "Estimating 3D pose and head orientation from 2D landmark correspondences"},
            {"key": "C", "text": "Applying bilateral blurring to reduce Gaussian noise"},
            {"key": "D", "text": "Performing morphological dilation on binary masks"}
        ],
        "correct": "B"
    },
    {
        "id": "q_cv_02",
        "category": "Computer Vision & AI",
        "question": "How does Eye Aspect Ratio (EAR) differentiate between an open eye and a blink?",
        "options": [
            {"key": "A", "text": "EAR drops rapidly below a calibrated threshold during eyelid closure"},
            {"key": "B", "text": "EAR measures pupil diameter in dark environments"},
            {"key": "C", "text": "EAR increases proportional to ambient screen luminance"},
            {"key": "D", "text": "EAR performs Fourier transform on corneal reflections"}
        ],
        "correct": "A"
    },
    {
        "id": "q_dsa_01",
        "category": "Data Structures & Algorithms",
        "question": "What is the average time complexity of searching in a balanced Binary Search Tree (AVL/Red-Black)?",
        "options": [
            {"key": "A", "text": "O(1)"},
            {"key": "B", "text": "O(log n)"},
            {"key": "C", "text": "O(n)"},
            {"key": "D", "text": "O(n log n)"}
        ],
        "correct": "B"
    },
    {
        "id": "q_os_02",
        "category": "Operating Systems",
        "question": "Which condition is NOT one of the four Coffman conditions necessary for deadlock to occur?",
        "options": [
            {"key": "A", "text": "Mutual Exclusion"},
            {"key": "B", "text": "Hold and Wait"},
            {"key": "C", "text": "Preemption of Resources"},
            {"key": "D", "text": "Circular Wait"}
        ],
        "correct": "C"
    },
    {
        "id": "q_net_01",
        "category": "Computer Networks",
        "question": "In the TCP/IP suite, which layer is responsible for end-to-end reliable delivery and flow control?",
        "options": [
            {"key": "A", "text": "Network Layer (IP)"},
            {"key": "B", "text": "Transport Layer (TCP)"},
            {"key": "C", "text": "Data Link Layer (Ethernet)"},
            {"key": "D", "text": "Application Layer (HTTP)"}
        ],
        "correct": "B"
    },
    {
        "id": "q_ai_01",
        "category": "Machine Learning & AI",
        "question": "What is the role of Non-Maximum Suppression (NMS) in object detection algorithms like YOLO?",
        "options": [
            {"key": "A", "text": "Eliminating duplicate, overlapping bounding boxes for the same detected object"},
            {"key": "B", "text": "Normalizing RGB pixel color intensities to range [0, 1]"},
            {"key": "C", "text": "Computing backpropagation gradient descent loss"},
            {"key": "D", "text": "Upsampling low-resolution feature maps"}
        ],
        "correct": "A"
    },
    {
        "id": "q_sec_01",
        "category": "Cybersecurity",
        "question": "Which cryptographic property ensures that a message cannot be tampered with in transit without detection?",
        "options": [
            {"key": "A", "text": "Integrity"},
            {"key": "B", "text": "Confidentiality"},
            {"key": "C", "text": "Availability"},
            {"key": "D", "text": "Non-repudiation"}
        ],
        "correct": "A"
    },
    {
        "id": "q_dsa_02",
        "category": "Data Structures & Algorithms",
        "question": "Which sorting algorithm guarantees O(n log n) worst-case time complexity with O(1) auxiliary memory?",
        "options": [
            {"key": "A", "text": "Merge Sort"},
            {"key": "B", "text": "Heap Sort"},
            {"key": "C", "text": "Quick Sort"},
            {"key": "D", "text": "Bubble Sort"}
        ],
        "correct": "B"
    },
    {
        "id": "q_db_01",
        "category": "Database Systems",
        "question": "What does the 'A' in ACID properties of relational database transactions represent?",
        "options": [
            {"key": "A", "text": "Authentication"},
            {"key": "B", "text": "Atomicity (All operations succeed or all rollback)"},
            {"key": "C", "text": "Asynchronous"},
            {"key": "D", "text": "Availability"}
        ],
        "correct": "B"
    },
    {
        "id": "q_os_03",
        "category": "Operating Systems",
        "question": "What is the primary benefit of Virtual Memory paging?",
        "options": [
            {"key": "A", "text": "Allows execution of processes whose address space exceeds available physical RAM"},
            {"key": "B", "text": "Eliminates the need for CPU cache memory"},
            {"key": "C", "text": "Speeds up disk input/output transfer rates"},
            {"key": "D", "text": "Replaces the need for instruction pipelining"}
        ],
        "correct": "A"
    },
    {
        "id": "q_cv_03",
        "category": "Computer Vision & AI",
        "question": "Which color space is most commonly utilized for skin-tone segmentation due to separating luminance from chrominance?",
        "options": [
            {"key": "A", "text": "RGB"},
            {"key": "B", "text": "YCbCr / HSV"},
            {"key": "C", "text": "Grayscale"},
            {"key": "D", "text": "CMYK"}
        ],
        "correct": "B"
    },
    {
        "id": "q_arch_02",
        "category": "Computer Architecture",
        "question": "What hazard in CPU pipelining occurs when instructions depend on the result of a previous instruction still in the pipeline?",
        "options": [
            {"key": "A", "text": "Structural Hazard"},
            {"key": "B", "text": "Data Hazard"},
            {"key": "C", "text": "Control Hazard"},
            {"key": "D", "text": "Branch Misprediction"}
        ],
        "correct": "B"
    }
]

SUBJECTIVE_QUESTION_BANK = [
    {
        "id": "sq_os_01",
        "category": "Operating Systems & Memory",
        "question": "Explain the concept of Virtual Memory Paging. Describe what happens step-by-step during a Page Fault when a process accesses a page that is not currently present in physical RAM.",
        "rubric": "Virtual memory divides address space into fixed-size pages mapped to physical frames via page tables. When an unmapped address is accessed, MMU triggers a page fault interrupt/trap. The OS kernel saves process state, locates the required page in swap/secondary storage, finds a free physical frame (running page replacement algorithms like LRU if full), reads disk into RAM, updates page table valid bit, and restarts the instruction.",
        "max_marks": 5.0
    },
    {
        "id": "sq_sec_01",
        "category": "Cybersecurity & Cryptography",
        "question": "Compare Symmetric vs Asymmetric Cryptography in terms of key distribution, computational speed, and security use-cases. How does TLS/HTTPS combine both for secure web communication?",
        "rubric": "Symmetric encryption uses a single shared secret key for encryption and decryption (e.g. AES), making it computationally fast for large payloads, but difficult to distribute keys securely. Asymmetric uses a public-private keypair (e.g. RSA, ECC), enabling secure key exchange and digital signatures but is slower. TLS/HTTPS uses asymmetric cryptography during the TLS handshake to authenticate the server and securely exchange a session key, then switches to symmetric encryption for fast bulk data transmission.",
        "max_marks": 5.0
    },
    {
        "id": "sq_cv_01",
        "category": "Computer Vision & AI",
        "question": "Explain the role of Convolutional Layers, Non-Linear Activation Functions (such as ReLU), and Pooling Layers in an image classification or object detection pipeline. Why are convolutions preferable over fully connected layers for raw image data?",
        "rubric": "Convolutional layers apply spatial filters/kernels to extract local visual features (edges, textures, shapes) while sharing weights and preserving spatial hierarchy. Activation functions like ReLU introduce non-linearity to learn complex patterns. Pooling layers (e.g. MaxPooling) downsample feature maps, reducing computational dimensionality and providing translational invariance. Convolutions are preferable because they drastically reduce parameter count and leverage spatial locality/translation equivariance compared to fully connected layers.",
        "max_marks": 5.0
    },
    {
        "id": "sq_db_01",
        "category": "Database Systems & Transactions",
        "question": "Explain the ACID properties of relational databases. Describe how the Two-Phase Locking (2PL) protocol ensures Serializability and prevents concurrency anomalies like Lost Updates.",
        "rubric": "ACID stands for Atomicity (all-or-nothing), Consistency (preserves integrity constraints), Isolation (concurrent transactions execute independently), and Durability (committed changes persist across crashes). Two-Phase Locking (2PL) has a Growing Phase (acquiring locks, no releases) and a Shrinking Phase (releasing locks, no new acquisitions). By ensuring no lock is acquired after any lock has been released, 2PL guarantees serializable schedules and prevents dirty reads, unrepeatable reads, and lost updates.",
        "max_marks": 5.0
    }
]


def _generate_subjective_from_gemini(num_questions=1, topic="Computer Science, Operating Systems, AI, and Software Engineering"):
    """
    Generates dynamic subjective writing questions with grading rubrics using Gemini AI.
    """
    api_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = (
            f"Generate exactly {num_questions} university-level conceptual writing / subjective exam question(s) on '{topic}'.\n"
            "Each question MUST have:\n"
            "- 'category': string topic name\n"
            "- 'question': a clear, thought-provoking technical question requiring 3-5 sentences of explanation\n"
            "- 'rubric': a comprehensive grading rubric / ideal answer summary containing all essential technical concepts\n"
            "- 'max_marks': 5.0\n"
            "Return ONLY valid JSON in this format: "
            "{\"questions\": [{\"category\": \"...\", \"question\": \"...\", \"rubric\": \"...\", \"max_marks\": 5.0}]}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )

        data = json.loads(response.text)
        raw_questions = data.get("questions", [])
        if not raw_questions:
            return None

        formatted = []
        for idx, q in enumerate(raw_questions[:num_questions], 1):
            formatted.append({
                "id": f"sq{idx}",
                "category": f"AI Generated: {q.get('category', 'Conceptual Writing')}",
                "question": q.get("question", ""),
                "rubric": q.get("rubric", ""),
                "max_marks": float(q.get("max_marks", 5.0))
            })
        return formatted

    except Exception as e:
        print(f"[INFO] Gemini Subjective Question Generation unavailable ({e}), using curated bank.")
        return None


def _generate_from_gemini(num_questions=3, topic="Computer Science, Operating Systems, AI, and Software Engineering"):
    """
    Generates dynamic exam questions using the Google Gemini API (gemini-2.5-flash).
    """
    api_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = (
            f"Generate exactly {num_questions} university-level multiple choice questions on '{topic}'.\n"
            "Each question MUST have:\n"
            "- 'category': string topic name\n"
            "- 'question': clear, unambiguous question text\n"
            "- 'options': list of 4 options with 'key' ('A', 'B', 'C', 'D') and 'text'\n"
            "- 'correct': the key ('A', 'B', 'C', or 'D') corresponding to the correct option\n"
            "Return ONLY valid JSON in this format: "
            "{\"questions\": [{\"category\": \"...\", \"question\": \"...\", \"options\": [{\"key\": \"A\", \"text\": \"...\"}, ...], \"correct\": \"A\"}]}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )

        data = json.loads(response.text)
        raw_questions = data.get("questions", [])
        if not raw_questions or len(raw_questions) < num_questions:
            return None

        questions = []
        answer_key = {}
        for idx, q in enumerate(raw_questions[:num_questions], 1):
            q_id = f"q{idx}"
            correct_key = q.get("correct", "A")
            opts = q.get("options", [])
            correct_text = ""
            for opt in opts:
                if opt.get("key") == correct_key:
                    correct_text = opt.get("text", "")
                    break
            if not correct_text and opts:
                correct_text = opts[0].get("text", "")

            random.shuffle(opts)
            remapped_options = []
            new_correct_key = "A"
            for opt_idx, key_char in enumerate(["A", "B", "C", "D"]):
                if opt_idx < len(opts):
                    orig_opt = opts[opt_idx]
                    opt_text = orig_opt.get("text", "")
                    remapped_options.append({"key": key_char, "text": opt_text})
                    if opt_text == correct_text:
                        new_correct_key = key_char
                else:
                    remapped_options.append({"key": key_char, "text": "None of the above"})

            answer_key[q_id] = new_correct_key
            questions.append({
                "id": q_id,
                "category": f"AI Generated: {q.get('category', 'Computer Science')}",
                "question": q.get("question", ""),
                "options": remapped_options
            })

        print("[OK] Dynamic Exam Questions generated successfully via Gemini AI.")
        return questions, answer_key

    except Exception as e:
        print(f"[INFO] Gemini AI Question Generation unavailable ({e}), proceeding to fallback.")
        return None


def _generate_from_open_source_api(num_questions=3):
    """
    Fetches real-time dynamic questions from the Open Trivia Database (Category 18: Computer Science).
    """
    try:
        url = f"https://opentdb.com/api.php?amount={num_questions}&category=18&type=multiple"
        res = requests.get(url, timeout=3.5)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if len(results) >= num_questions:
                questions = []
                answer_key = {}
                for idx, item in enumerate(results[:num_questions], 1):
                    q_id = f"q{idx}"
                    category = html.unescape(item.get("category", "Computer Science"))
                    question_text = html.unescape(item.get("question", ""))
                    correct_answer = html.unescape(item.get("correct_answer", ""))
                    incorrect_answers = [html.unescape(ans) for ans in item.get("incorrect_answers", [])]

                    all_opts = [correct_answer] + incorrect_answers[:3]
                    random.shuffle(all_opts)

                    remapped_options = []
                    new_correct_key = "A"
                    for opt_idx, key_char in enumerate(["A", "B", "C", "D"]):
                        if opt_idx < len(all_opts):
                            opt_text = all_opts[opt_idx]
                            remapped_options.append({"key": key_char, "text": opt_text})
                            if opt_text == correct_answer:
                                new_correct_key = key_char
                        else:
                            remapped_options.append({"key": key_char, "text": "None of the above"})

                    answer_key[q_id] = new_correct_key
                    questions.append({
                        "id": q_id,
                        "category": f"Live Feed: {category}",
                        "question": question_text,
                        "options": remapped_options
                    })
                print("[OK] Dynamic Exam Questions fetched successfully via Open Source API.")
                return questions, answer_key
    except Exception as e:
        print(f"[INFO] Open-source question API unavailable ({e}), using local bank.")
    return None


def _generate_from_local_bank(num_questions=3):
    """
    Returns a randomized, option-shuffled subset of questions from the offline curated question bank.
    """
    selected = random.sample(QUESTION_BANK, min(num_questions, len(QUESTION_BANK)))
    shuffled_questions = []
    answer_key = {}

    for idx, q in enumerate(selected, 1):
        q_id = f"q{idx}"
        correct_text = ""
        for opt in q["options"]:
            if opt["key"] == q["correct"]:
                correct_text = opt["text"]
                break

        opts = list(q["options"])
        random.shuffle(opts)

        remapped_options = []
        new_correct_key = "A"
        for opt_idx, key_char in enumerate(["A", "B", "C", "D"]):
            orig_opt = opts[opt_idx]
            remapped_options.append({"key": key_char, "text": orig_opt["text"]})
            if orig_opt["text"] == correct_text:
                new_correct_key = key_char

        answer_key[q_id] = new_correct_key
        shuffled_questions.append({
            "id": q_id,
            "category": q["category"],
            "question": q["question"],
            "options": remapped_options
        })

    return shuffled_questions, answer_key


def generate_random_exam(num_mcq=3, num_subjective=1, topic="Computer Science, Operating Systems, AI, and Software Engineering"):
    """
    Primary Question Generation Dispatcher:
    Returns (mcq_questions, mcq_answer_key, subjective_questions).
    """
    # 1. Generate MCQs (Gemini -> Open-Source API -> Local Bank)
    mcq_result = _generate_from_gemini(num_mcq, topic)
    if mcq_result is None:
        mcq_result = _generate_from_open_source_api(num_mcq)
    if mcq_result is None:
        mcq_result = _generate_from_local_bank(num_mcq)

    mcq_questions, mcq_answer_key = mcq_result

    # 2. Generate Subjective Writing Questions (Gemini -> Local Bank)
    subjective_questions = None
    if num_subjective > 0:
        subjective_questions = _generate_subjective_from_gemini(num_subjective, topic)
        if not subjective_questions:
            selected_sub = random.sample(SUBJECTIVE_QUESTION_BANK, min(num_subjective, len(SUBJECTIVE_QUESTION_BANK)))
            subjective_questions = []
            for idx, sq in enumerate(selected_sub, 1):
                subjective_questions.append({
                    "id": f"sq{idx}",
                    "category": sq["category"],
                    "question": sq["question"],
                    "rubric": sq["rubric"],
                    "max_marks": sq.get("max_marks", 5.0)
                })

    return mcq_questions, mcq_answer_key, subjective_questions or []



