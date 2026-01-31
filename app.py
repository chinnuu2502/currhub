from flask import Flask, render_template, request, jsonify, send_file
import requests
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

MODEL_ID = "granite3.3:2b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

LATEST_CURRICULUM = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/generate-curriculum", methods=["POST"])
def generate():
    global LATEST_CURRICULUM

    data = request.json
    skill = data.get("skill")
    level = data.get("level")
    semesters = data.get("semesters")

    prompt = f"""
Generate a curriculum in STRICT JSON format.

Fields required:
title
level
semesters (array)

Each semester must have:
name
courses (array)

Each course must have:
course_name
credits (number)
topics (array)

Skill: {skill}
Level: {level}
Semesters: {semesters}

Return ONLY valid JSON.
"""

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": MODEL_ID, "prompt": prompt, "stream": False},
            timeout=120
        )

        result = response.json()["response"]
        curriculum = json.loads(result)

        LATEST_CURRICULUM = curriculum
        return jsonify(curriculum)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/download-json")
def download_json():
    with open("curriculum.json", "w") as f:
        json.dump(LATEST_CURRICULUM, f, indent=4)
    return send_file("curriculum.json", as_attachment=True)


@app.route("/api/download-pdf")
def download_pdf():
    file_name = "curriculum.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    text = c.beginText(40, 800)

    text.textLine(LATEST_CURRICULUM.get("title", "Curriculum"))
    text.textLine("")

    for sem in LATEST_CURRICULUM.get("semesters", []):
        text.textLine(sem["name"])
        for course in sem["courses"]:
            text.textLine(f"  {course['course_name']} ({course['credits']} credits)")
            for topic in course["topics"]:
                text.textLine(f"    - {topic}")
        text.textLine("")

    c.drawText(text)
    c.save()
    return send_file(file_name, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
