"""
Dynamic Exam Question Bank.
Author: Sole Contributor / Creator
Provides a comprehensive bank of computer science, AI, OS, and software engineering questions.
Generates randomized problem sets for every candidate session.
"""

import random

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

def generate_random_exam(num_questions=4):
    """
    Returns a fresh randomized subset of questions and the corresponding answer key.
    """
    selected = random.sample(QUESTION_BANK, min(num_questions, len(QUESTION_BANK)))
    # Shuffle options for each selected question
    shuffled_questions = []
    answer_key = {}

    for idx, q in enumerate(selected, 1):
        q_id = f"q{idx}"
        correct_text = ""
        for opt in q["options"]:
            if opt["key"] == q["correct"]:
                correct_text = opt["text"]
                break

        # Create copy of options and shuffle keys
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
