 DOOMSTUDY — AI Interview Arena

DOOMSTUDY is an AI-powered interview preparation platform built with Flask and Groq AI. 
It generates technical interview questions, evaluates answers with AI-generated feedback and scores,
and tracks performance through analytics and interview history — all inside a DOOM-inspired interface.

---

 Features

 AI-generated interview questions
 AI answer evaluation with scores
 Analytics dashboard
 Interview history tracking
 Session memory support
 SQLite database integration
 Rate limiting and logging
 DOOM-inspired UI

---

 Tech Stack

 Python
 Flask
 Groq API
 SQLite
 HTML/CSS/JavaScript

---

 Installation

```bash
git clone https://github.com/m4ryan07/Doomstudy.git
cd Doomstudy
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key
SECRET_KEY=your_secret_key
```

Run the app:

```bash
python app.py
```

---

Routes

| Route        | Description         |
| ------------ | ------------------- |
| `/`          | Home page           |
| `/history`   | Interview history   |
| `/dashboard` | Analytics dashboard |
| `/memory`    | Session memory      |

---

 Future Improvements

 Resume analysis
 Voice interviews
 AI follow-up questions
 PDF reports
 User authentication







 Author

Built by M Aryan.
