import json
import os
import re
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from openai import OpenAI
from .models import Lead

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple memory
user_state = {}


# ---------------- HOME ----------------
def home(request):
    return render(request, "index.html")


# ---------------- CHAT API ----------------
@csrf_exempt
def chat_api(request):

    if request.method != "POST":
        return JsonResponse({"reply": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()
    except:
        return JsonResponse({"reply": "Invalid data"}, status=400)

    if not message:
        return JsonResponse({"reply": "Please enter a message."})

    msg = message.lower()
    user_id = "default"

    if user_id not in user_state:
        user_state[user_id] = {"mode": "chat"}

    state = user_state[user_id]

    # ---------------- COURSE DATA ----------------
    courses = {
        "python": {"duration": "3 months", "fee": "₹15,000"},
        "django": {"duration": "2 months", "fee": "₹12,000"},
        "react": {"duration": "2 months", "fee": "₹12,000"},
        "mern": {"duration": "4 months", "fee": "₹25,000"},
        "full stack": {"duration": "6 months", "fee": "₹40,000"}
    }

    # ---------------- GREETING ----------------
    if msg in ["hi", "hello", "hey"]:
        return JsonResponse({
            "reply": "Hi 👋 Welcome!\n\nYou can ask:\n• list of available courses\n• Fees and duration\n• Enroll"
        })

    if "thank" in msg:
        return JsonResponse({"reply": "You're welcome 😊"})

    if msg in ["bye", "exit"]:
        user_state[user_id] = {"mode": "chat"}
        return JsonResponse({"reply": "Goodbye 👋"})

    # ---------------- NEW ADDITIONS (ONLY THIS PART) ----------------

    # ✔ what courses do you offer
    if "what courses do you offer" in msg:
        msg = "list courses"

    # ✔ help me choose course
    if "help me choose" in msg or "choose a course" in msg:
        return JsonResponse({
            "reply": "If you're a beginner, Python is a great start.\nIf you want web development, you can choose MERN or Full Stack.\n\n👉 Which one interests you?"
        })

    # ✔ tell me about python / mern etc
    if "tell me about" in msg:
        for course in courses:
            if course in msg:
                msg = course  # redirect to existing logic

    # ---------------- LIST COURSES ----------------
    if "list" in msg or "courses" in msg:
        reply = (
            "📚 Available Courses:\n\n"
            "• Python (3 months) — ₹15,000\n"
            "• Django (2 months) — ₹12,000\n"
            "• React (2 months) — ₹12,000\n"
            "• MERN Stack (4 months) — ₹25,000\n"
            "• Full Stack (6 months) — ₹40,000\n\n"
            "👉 Which course are you interested in?"
        )
        return JsonResponse({"reply": reply})

    # ---------------- SPECIFIC COURSE ----------------
    for course in courses:
        if course in msg:
            c = courses[course]
            state["selected_course"] = course

            return JsonResponse({
                "reply": f"📘 {course.title()} Course\n\nDuration: {c['duration']}\nFees: {c['fee']}\n\n👉 Do you want to enroll?"
            })

    # ---------------- ENROLL ----------------
    if "yes" in msg and "selected_course" in state:
        state["mode"] = "lead"
        state["step"] = 1

        return JsonResponse({
            "reply": "Great 😊 Let's register you.\n\nWhat is your name?"
        })

    # ---------------- LEAD FLOW ----------------
    if state.get("mode") == "lead":

        if state.get("step") == 1:

            if len(message) < 2 or any(char.isdigit() for char in message):
                return JsonResponse({"reply": "Please enter a valid name."})

            state["name"] = message
            state["step"] = 2

            return JsonResponse({"reply": "Enter your phone number (10 digits)"})

        elif state.get("step") == 2:

            if not re.fullmatch(r"\d{10}", message):
                return JsonResponse({"reply": "Enter a valid 10-digit phone number."})

            try:
                Lead.objects.create(
                    name=state["name"],
                    phone=message,
                    interest=state.get("selected_course", "General")
                )

                reply = "✅ Registered successfully! We will contact you."

            except Exception as e:
                print(e)
                reply = "Error saving details."

            user_state[user_id] = {"mode": "chat"}

            return JsonResponse({"reply": reply})

    # ---------------- AI FALLBACK ----------------
    try:
        ai = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for courses."},
                {"role": "user", "content": message}
            ]
        )

        reply = ai.choices[0].message.content.strip()

    except:
        reply = "Ask about courses, fees, or enrollment 😊"

    return JsonResponse({"reply": reply})