# 📄 AI Resume Reviewer & Job Match Scorer

A production-quality GenAI web application that analyzes resumes against job descriptions using LLM-powered semantic analysis and deterministic scoring.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-ff4b4b?logo=streamlit&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-LCEL-green?logo=chainlink&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-e92063?logo=pydantic&logoColor=white)

---

## 🎯 Project Overview

**Problem:** Manually comparing a resume against a job description is time-consuming and subjective. Key skill gaps and keyword mismatches are easy to miss.

**Solution:** This application uses Generative AI (via OpenAI's API) to perform deep semantic analysis of a resume against a job description, then applies a deterministic scoring system to produce a reproducible, explainable match score.

The LLM provides the **semantic judgment** (identifying matched/missing skills, evaluating experience, etc.), while the **final score is calculated programmatically** — ensuring reproducibility and transparency.

---

## ✨ Features

| Feature | Description |
|---|---|
| **PDF Resume Upload** | Upload any PDF resume via drag-and-drop |
| **PyPDFLoader Integration** | Extracts text from single and multi-page PDFs |
| **LLM Semantic Analysis** | Deep comparison of resume vs. job description |
| **Structured Output** | Pydantic-validated JSON output from the LLM |
| **Deterministic Scoring** | Weighted scoring system with transparent breakdown |
| **Skill Matching** | Identifies matched and missing skills |
| **Keyword Analysis** | Matched and missing keyword identification |
| **Experience Analysis** | Compares candidate experience to requirements |
| **Education Analysis** | Evaluates educational qualifications |
| **Project Relevance** | Assesses project portfolio against job needs |
| **Strengths & Weaknesses** | Concrete, actionable feedback |
| **Resume Improvements** | Specific suggestions (never recommends lying) |
| **Interview Preparation** | Targeted topics based on gaps and requirements |
| **Downloadable Reports** | Export as JSON or formatted TXT |
| **Error Handling** | Graceful handling of all failure modes |

---

## 🏗️ Architecture

```
Resume PDF
    ↓
PyPDFLoader (text extraction)
    ↓
Text Cleaning & Normalization
    ↓                              Job Description (user input)
    ↓                                       ↓
    └──────────────→ LangChain LCEL Chain ←─┘
                     (prompt | llm | parser)
                            ↓
                   PydanticOutputParser
                            ↓
                   ResumeAnalysis (validated)
                            ↓
                   Deterministic Scoring
                            ↓
                   ScoreBreakdown
                            ↓
                   Streamlit Dashboard + Downloads
```

### Module Structure

```
ai-resume-reviewer/
│
├── app.py                 # Streamlit UI application
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .gitignore
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── schemas.py         # Pydantic models (ResumeAnalysis, ScoreBreakdown, etc.)
│   ├── pdf_loader.py      # PDF upload handling and text extraction
│   ├── text_processing.py # Text cleaning, normalization, truncation
│   ├── prompts.py         # LLM prompt templates (system + human)
│   ├── llm_chain.py       # LCEL chain (prompt | llm | parser) + retry logic
│   ├── scoring.py         # Deterministic weighted scoring engine
│   └── utils.py           # Report generation, color helpers
│
└── tests/
    ├── test_scoring.py    # Scoring calculation unit tests
    └── test_schemas.py    # Pydantic validation unit tests
```

---

## 🔧 Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core language |
| **Streamlit** | Web UI framework |
| **LangChain** | LLM orchestration framework |
| **LangChain LCEL** | Expression language for chain composition (`prompt \| llm \| parser`) |
| **LangChain Google GenAI** | Google Gemini API integration |
| **PydanticOutputParser** | Forces structured JSON output from the LLM |
| **Pydantic v2** | Data validation and serialization |
| **PyPDFLoader** | PDF text extraction |
| **python-dotenv** | Environment variable management |

---

## 🚀 Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ai-resume-reviewer
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Get your free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:

```env
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

> **Note:** You can also enter or override the API key directly in the Streamlit sidebar UI at runtime.

### 5. Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 📖 Usage

1. **Upload Resume** — Click "Browse files" and select your PDF resume.
2. **Paste Job Description** — Copy the full JD into the text area.
3. **Configure** — Adjust model, temperature, and API key in the sidebar.
4. **Analyze** — Click "🔍 Analyze Resume" and wait for results.
5. **Review** — Explore the dashboard: scores, skills, keywords, analysis.
6. **Download** — Export the full report as JSON or TXT.

---

## 📊 Scoring System

The scoring system is **deterministic and transparent**. The LLM provides semantic sub-scores (0–100) for each category, and this module applies fixed weights:

| Category | Weight | Max Score |
|---|---|---|
| Skill Match | 40% | 40 |
| Keyword Match | 20% | 20 |
| Experience Match | 20% | 20 |
| Education Match | 10% | 10 |
| Project Match | 10% | 10 |
| **Total** | **100%** | **100** |

**Match Levels:**
- 🟢 **Strong Match**: ≥ 75/100
- 🟡 **Moderate Match**: ≥ 50/100
- 🔴 **Weak Match**: < 50/100

### Example Breakdown

```
Skill Match:       34.0/40  (raw: 85/100)
Keyword Match:     16.0/20  (raw: 80/100)
Experience Match:  15.0/20  (raw: 75/100)
Education Match:    8.0/10  (raw: 80/100)
Project Match:      9.0/10  (raw: 90/100)
─────────────────────────────────────────
TOTAL:             82.0/100  (Strong Match)
```

---

## 📋 Example JSON Output

```json
{
  "resume_analysis": {
    "matched_skills": ["Python", "Machine Learning", "SQL", "TensorFlow", "Git"],
    "missing_skills": ["Docker", "AWS", "Kubernetes"],
    "matched_keywords": ["REST API", "Data Analysis", "Deep Learning"],
    "missing_keywords": ["CI/CD", "Cloud Computing", "Microservices"],
    "experience_match": "Candidate has 3 years of ML experience, matching the 2+ year requirement.",
    "education_match": "B.S. in Computer Science aligns with the required technical degree.",
    "project_relevance": "ML classification project directly relevant to the role's NLP requirements.",
    "strengths": [
      "Strong Python and ML foundation",
      "Hands-on TensorFlow experience",
      "Published ML project on GitHub"
    ],
    "weaknesses": [
      "No containerization or DevOps experience",
      "No cloud platform exposure (AWS, GCP, Azure)"
    ],
    "suggested_improvements": [
      "Add quantified impact to project descriptions",
      "Highlight REST API development experience more prominently"
    ],
    "suggested_keywords_to_emphasize": ["Python", "Machine Learning", "TensorFlow"],
    "suggested_keywords_to_learn": ["Docker", "AWS", "CI/CD"],
    "interview_topics": ["Python OOP", "ML model evaluation", "REST API design"],
    "skill_match_score": 85,
    "keyword_match_score": 80,
    "experience_match_score": 75,
    "education_match_score": 80,
    "project_match_score": 90
  },
  "score_breakdown": {
    "skill_match_raw": 85.0,
    "skill_match_weighted": 34.0,
    "keyword_match_raw": 80.0,
    "keyword_match_weighted": 16.0,
    "experience_match_raw": 75.0,
    "experience_match_weighted": 15.0,
    "education_match_raw": 80.0,
    "education_match_weighted": 8.0,
    "project_match_raw": 90.0,
    "project_match_weighted": 9.0,
    "overall_score": 82.0,
    "match_level": "Strong Match"
  },
  "resume_filename": "john_doe_resume.pdf",
  "analysis_timestamp": "2024-12-01T14:32:00.000000"
}
```

---

## 🧪 Running Tests

```bash
cd ai-resume-reviewer
python -m pytest tests/ -v
```

**Test coverage includes:**
- Score calculation (0%, 50%, 100% matches)
- Boundary conditions and clamping
- Weight validation (must sum to 100)
- Pydantic schema validation
- Missing fields handling
- JSON serialization
- Match level thresholds

---

## 🧠 GenAI Concepts Demonstrated

This project demonstrates proper GenAI engineering practices:

| Concept | Implementation |
|---|---|
| **Large Language Models** | OpenAI GPT-4o-mini / GPT-4o for semantic analysis |
| **Prompt Engineering** | Detailed system prompt with role, principles, and scoring rubric |
| **LangChain** | Framework for LLM orchestration and tooling |
| **LCEL (LangChain Expression Language)** | `prompt \| llm \| parser` pipeline composition |
| **Structured Output** | LLM forced to return Pydantic-validated JSON |
| **Pydantic** | Data validation, type enforcement, score clamping |
| **PydanticOutputParser** | LangChain parser that enforces schema compliance |
| **Document Loading** | PyPDFLoader for PDF text extraction |
| **Semantic Matching** | LLM identifies conceptual (not just keyword) matches |
| **Deterministic Scoring** | Programmatic, weighted scoring — NOT LLM-decided |
| **Error Handling** | Retry logic, graceful degradation, user-friendly errors |
| **Modular Architecture** | Clean separation of concerns across 7 modules |

---

## 📄 License

This project is intended as a portfolio demonstration. Feel free to use and modify.
