# 📘 LeetJournal – Track Your LeetCode Journey

> A cozy, personalized journal to track, reflect, and grow with your daily LeetCode grind.

---

## ✨ Overview

**LeetJournal** is a web app designed to help developers track their LeetCode problem-solving journey. Whether you're preparing for interviews, trying to stay consistent, or revising old problems, LeetJournal gives you a clear, calm space to:

- ✍️ Take notes on solved problems  
- 🗂️ Organize questions with tags and difficulty  
- 🗓️ View your solving history on a calendar  
- 🔍 Search and filter problems easily  
- 🖼️ Upload images like hand-drawn graphs  
- 🌐 Auto-fetch metadata from LeetCode URLs

---

## 🔧 Tech Stack

| Frontend | Backend | Database | Media Storage | Deployment |
|---------|---------|----------|----------------|------------|
| HTML, Tailwind CSS (Via CLI), JS | Django | PostgreSQL hosted on Supabase | Cloudinary | Render |

---

## 🚀 Features

- **📥 Auto-Fetch LeetCode Metadata**  
  Paste a LeetCode URL and instantly fetch title, difficulty, and tags.

- **📌 Smart Journal System**  
  Log solutions, add multiple text fields (e.g., name, email), and upload related images.

- **🗃️ Tag & Difficulty Filtering**  
  Organize entries with custom tags and revisit hard problems.

- **🗓️ Interactive Calendar**  
  View which questions were solved on which day—perfect for consistency tracking.

- **🔍 Advanced Search**  
  Search by title, tag, difficulty, or date solved.

- **🧠 Revision Support**  
  Mark problems for revision and revisit them anytime.

---

## 🖼️ UI Preview

| Home Page | Question View | Search Based On Filter |
|-----------|----------------|----------|
| ![Home](./assets/Screenshot%202025-06-03%20182709.png) | ![View](./assets/Screenshot%202025-06-01%20215638.png) | ![Calendar](./assets/Screenshot%202025-06-01%20215621.png) |

---

## ⚙️ Installation

1. **Clone the Repository**

```bash
git clone https://github.com/mohdsaabir/leetjournal.git
cd leetjournal
```

2. **Set up the Environment**

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

3. **Configure Environment Variables**

```bash
DEBUG=True
SECRET_KEY=your_django_secret
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
DATABASE_URL=postgres://user:password@localhost:5432/leetjournal
```

4 **Run Migrations And Start Server**

```bash
python manage.py migrate
python manage.py runserver
```

---

## 🌍 Live Demo
🔗 https://leetjournal.onrender.com


