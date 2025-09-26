from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import date
from typing import Dict, List

def draw_wrapped_string(c, x, y, text, max_width, font_name="Helvetica", font_size=12, leading=14):
    c.setFont(font_name, font_size)
    words = text.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            c.drawString(x, y, line.rstrip())
            y -= leading
            line = word + " "
    if line:
        c.drawString(x, y, line.rstrip())
        y -= leading
    return y


def generate_reason_based_on_level(level: str) -> str:
    if level == "beginner":
        return (
            "Because of your beginner experience, it is important to start with foundational courses that cover the core concepts and basic skills. "
            "These courses will help you build a strong understanding of the fundamentals, enabling you to progress confidently. "
            "Focus on mastering the basics and practical applications before moving to advanced topics. "
            "This solid foundation will prepare you for more complex learning paths and career opportunities. "
            "Take your time with each module and practice consistently to gain confidence and competence."
        )
    elif level == "intermediate":
        return (
            "As you have intermediate experience, these courses are carefully selected to strengthen your core skills and fill any knowledge gaps. "
            "They will deepen your theoretical understanding and enhance your practical abilities. "
            "The study plan focuses on consolidating your existing knowledge while introducing advanced concepts gradually. "
            "It will prepare you to solve more complex problems and handle real-world challenges effectively. "
            "Supplement your learning with hands-on projects to solidify your skills and demonstrate proficiency."
        )
    elif level == "advanced":
        return (
            "With advanced expertise, these courses are designed to help you master specialist topics and cutting-edge concepts in your field. "
            "The curriculum emphasizes deep dives into complex subject areas, latest industry practices, and emerging technologies. "
            "You will be challenged to apply your knowledge creatively and innovatively to advanced scenarios and projects. "
            "This study plan aims to broaden your horizons and develop leadership in specialized domains. "
            "Engage in research, case studies, and collaborations to stay ahead in your career and continuously grow."
        )
    else:
        return (
            "These courses are recommended based on your experience level to help you progress logically. "
            "They cover essential topics and guide you through a structured learning journey. "
            "Focus on steady learning and apply knowledge practically for best outcomes. "
            "Stay consistent and leverage these courses to achieve your career goals."
        )


def generate_pdf(path: str, goal: str, plan: List[Dict], gap_map: Dict[str, int], weeks: int,
                 level: str = None, skills: List[str] = None, notes: str = None, timeline: List[Dict] = None):
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    margin_x = 2 * cm
    current_y = height - 2 * cm
    line_height = 14
    max_width = width - 4 * cm 

    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin_x, current_y, "Upskill Advisor Study Plan")
    current_y -= 2 * line_height

    c.setFont("Helvetica-Bold", 14)
    label_role = "Target Role:"
    label_width = c.stringWidth(label_role, "Helvetica-Bold", 14)
    c.drawString(margin_x, current_y, label_role)
    c.setFont("Helvetica", 12)
    c.drawString(margin_x + label_width + 5, current_y, goal)
    current_y -= 1.5 * line_height

    if level:
        label_level = "Experience Level:"
        label_width = c.stringWidth(label_level, "Helvetica-Bold", 14)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin_x, current_y, label_level)
        c.setFont("Helvetica", 12)
        c.drawString(margin_x + label_width + 5, current_y, level.capitalize())
        current_y -= 1.5 * line_height

    if skills:
        label_skills = "Current Skills:"
        label_width = c.stringWidth(label_skills, "Helvetica-Bold", 14)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin_x, current_y, label_skills)
        c.setFont("Helvetica", 12)
        skill_text = ", ".join(skills)
        current_y = draw_wrapped_string(c, margin_x + label_width + 5, current_y, skill_text, max_width - label_width - 10)
        current_y -= line_height
    else:
        current_y -= line_height

    reason_text = generate_reason_based_on_level(level)
    c.setFont("Helvetica-Oblique", 12)
    current_y = draw_wrapped_string(c, margin_x, current_y, reason_text, max_width)
    current_y -= line_height

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x, current_y, "Recommended Courses")
    current_y -= 1.5 * line_height

    c.setFont("Helvetica", 12)
    for idx, item in enumerate(plan[:3], 1):
        c.setFont("Helvetica-Bold", 13)
        title = item.get('title', item.get('course_id', 'N/A'))
        difficulty = item.get('difficulty', 'N/A').capitalize()
        c.drawString(margin_x, current_y, f"{idx}. {title} ({difficulty})")
        current_y -= 1.2 * line_height

        why_text = "Why: " + item.get('why', "No specific reason given.")
        c.setFont("Helvetica-Oblique", 11)
        current_y = draw_wrapped_string(c, margin_x + 10, current_y, why_text, max_width - 10)
        current_y -= 0.5 * line_height

        outcomes = item.get('outcomes', [])
        if outcomes:
            c.setFont("Helvetica", 11)
            c.drawString(margin_x + 10, current_y, "Outcomes:")
            current_y -= 1.2 * line_height
            for out in outcomes:
                current_y = draw_wrapped_string(c, margin_x + 20, current_y, f"• {out}", max_width - 20)
                current_y -= 0.8 * line_height
        else:
            current_y -= line_height / 2

        current_y -= line_height / 2

    # Skill Gaps
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x, current_y, "Skill Gaps to Cover")
    current_y -= 1.5 * line_height
    c.setFont("Helvetica", 12)

    gap_skills = [k for k in gap_map if gap_map[k] > 0]
    if gap_skills:
        gap_intro = "Apart from these courses, the following skill gaps should also be covered:"
        current_y = draw_wrapped_string(c, margin_x, current_y, gap_intro, max_width)
        gap_text = ", ".join(gap_skills)
        current_y = draw_wrapped_string(c, margin_x, current_y, gap_text, max_width)
        current_y -= line_height
    else:
        c.drawString(margin_x, current_y, "No major skill gaps detected.")
        current_y -= line_height

    # Estimated Timeline and Weekly Study Plan
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x, current_y, "Estimated Timeline & Weekly Study Plan")
    current_y -= 1.5 * line_height

    c.setFont("Helvetica", 12)
    c.drawString(margin_x + 8, current_y, f"Total Duration: {weeks} week{'s' if weeks > 1 else ''}")
    current_y -= 1.5 * line_height

    if timeline:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, current_y, "Weekly Course Schedule:")
        current_y -= 1.2 * line_height

        c.setFont("Helvetica", 11)
        for entry in timeline:
            title = entry.get("title", entry.get("course_id", "N/A"))
            start = entry.get("start_week", 0)
            end = entry.get("end_week", 0)
            timeline_str = f"Weeks {start} to {end}: {title}"
            current_y = draw_wrapped_string(c, margin_x + 10, current_y, timeline_str, max_width)
            current_y -= 0.8 * line_height
            if current_y < 80:
                c.showPage()
                current_y = height - 2 * cm
    # Notes
    if notes:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin_x, current_y, "Notes")
        current_y -= 1.5 * line_height

        c.setFont("Helvetica-Oblique", 12)
        text_lines = notes.split('\n')
        for line in text_lines:
            current_y = draw_wrapped_string(c, margin_x + 8, current_y, line, max_width)
            current_y -= line_height
            if current_y < 80:
                c.showPage()
                current_y = height - 2 * cm

    c.showPage()
    c.save()
