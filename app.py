from flask import Flask, render_template, request, send_file
from groq import Groq
from fpdf import FPDF
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/analyze', methods=['POST'])
def analyze():

    # ---------------- BASIC INPUTS ----------------
    cycle_length = int(request.form.get('cycle_length', 0))
    period_duration = int(request.form.get('period_duration', 0))
    flow_level = int(request.form.get('flow_level', 1))

    energy = int(request.form.get('energy', 3))
    sleep = int(request.form.get('sleep', 6))
    water = int(request.form.get('water', 6))

    symptoms = request.form.getlist('symptoms')
    activity = request.form.get('activity', 'Moderate')

    # ---------------- PCOS SCORE ----------------
    pcos_score = 0
    if cycle_length > 35 or cycle_length < 24:
        pcos_score += 40
    if "irregular_periods" in symptoms:
        pcos_score += 40
    if "acne" in symptoms:
        pcos_score += 20
    if "hair_fall" in symptoms:
        pcos_score += 20
    if activity.lower() == "sedentary":
        pcos_score += 10
    pcos_score = min(pcos_score, 100)

    # ---------------- ANEMIA SCORE ----------------
    anemia_score = 0
    if flow_level == 3:
        anemia_score += 40
    if period_duration >= 6:
        anemia_score += 40
    if "fatigue" in symptoms:
        anemia_score += 20
    anemia_score = min(anemia_score, 100)

    # ---------------- LIFESTYLE SCORE ----------------
    lifestyle_score = 100
    if activity.lower() == "sedentary":
        lifestyle_score -= 30
    if sleep < 6:
        lifestyle_score -= 20
    if water < 5:
        lifestyle_score -= 20
    lifestyle_score = max(lifestyle_score, 0)

    # ---------------- HYDRATION SCORE ----------------
    hydration_score = min(water * 10, 100)

    # ---------------- SLEEP SCORE ----------------
    if sleep >= 8:
        sleep_score = 100
    elif sleep >= 6:
        sleep_score = 70
    elif sleep >= 4:
        sleep_score = 40
    else:
        sleep_score = 20

    # ------------------------------------------------
    # STRUCTURED AI SUMMARY (SUPER CLEAN & FORMATTED)
    # ------------------------------------------------
    summary = f"""
<h3><b>Cycle Interpretation</b></h3>
• Your cycle length is <b>{cycle_length} days</b> (Healthy range: 24–35 days).<br><br>

<h3><b>Period Duration</b></h3>
• Your period lasts <b>{period_duration} days</b> (Normal range: 3–7 days).<br><br>

<h3><b>Symptoms Review</b></h3>
• Reported symptoms: <b>{", ".join(symptoms) if symptoms else "None"}</b><br><br>

<h3><b>Activity Level</b></h3>
• Your activity level is <b>{activity.capitalize()}</b>.<br><br>

<h3><b>Health Risk Analysis</b></h3>
• <b>PCOS Risk Score:</b> {pcos_score}/100 — {"⚠ Possible symptoms detected. Monitor closely." if pcos_score > 60 else "✓ Normal risk level."}<br>
• <b>Anemia Risk Score:</b> {anemia_score}/100 — {"⚠ Heavy bleeding + fatigue may indicate low iron." if anemia_score > 60 else "✓ Looks normal."}<br>
• <b>Lifestyle Score:</b> {lifestyle_score}/100 — {"⚠ You should improve sleep/water/activity habits." if lifestyle_score < 60 else "✓ Your habits look balanced."}<br>
• <b>Hydration Score:</b> {hydration_score}/100<br>
• <b>Sleep Quality Score:</b> {sleep_score}/100<br><br>

<h3><b>Overall Summary</b></h3>
• Your menstrual health is <b>mostly stable</b> with some areas to monitor.<br>
• Tracking regularly will help you understand your pattern better.<br>
• If symptoms persist or worsen, a checkup is recommended.<br>
"""

    return render_template(
        'result.html',
        cycle_length=cycle_length,
        period_duration=period_duration,
        flow_level=flow_level,
        symptoms=symptoms,
        activity=activity,

        pcos_score=pcos_score,
        anemia_score=anemia_score,
        lifestyle_score=lifestyle_score,
        hydration_score=hydration_score,
        sleep_score=sleep_score,

        summary=summary
    )


# ---------------- PDF GENERATION ----------------
@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    summary_html = request.form.get("summary", "")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_text_color(255, 105, 180)
    pdf.cell(0, 10, "Menstrual Health Report", ln=True)

    pdf.set_text_color(0, 0, 0)
    clean_text = summary_html.replace("<br>", "\n") \
                             .replace("<h3>", "").replace("</h3>", "") \
                             .replace("<b>", "").replace("</b>", "")

    pdf.multi_cell(0, 8, clean_text)

    pdf.output("report.pdf")
    return send_file("report.pdf", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
