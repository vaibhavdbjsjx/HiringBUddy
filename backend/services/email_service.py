"""
Server-side email system (SMTP).

Single source of truth for outbound email so delivery works on deploy without
depending on public client-side keys. Falls back to a logged "mock" send when no
SMTP credentials are configured, so local/dev never crashes.

Templates render to premium, responsive, inline-styled HTML that survives email
clients (tables + inline CSS, no external assets).
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from config import settings

logger = logging.getLogger("hiringbuddy.email")

# Common provider SMTP hosts (host, port) keyed by domain fragment.
_SMTP_HOSTS = {
    "gmail.com": ("smtp.gmail.com", 587),
    "outlook.com": ("smtp.office365.com", 587),
    "hotmail.com": ("smtp.office365.com", 587),
    "yahoo.com": ("smtp.mail.yahoo.com", 587),
    "zoho.com": ("smtp.zoho.com", 587),
}

BRAND = "#ea580c"        # burnt orange
BRAND_2 = "#c2410c"      # deep orange


def _resolve_smtp(settings_obj) -> tuple[str, int, str, str, str]:
    """Return (host, port, username, password, sender_name)."""
    host, port = settings.SMTP_SERVER, settings.SMTP_PORT
    username, password = settings.SMTP_USERNAME, settings.SMTP_PASSWORD
    sender_name = "HiringBuddy AI"

    if settings_obj and settings_obj.smtp_email and settings_obj.smtp_password:
        username = settings_obj.smtp_email
        password = settings_obj.smtp_password
        sender_name = settings_obj.sender_name or sender_name
        for frag, (h, p) in _SMTP_HOSTS.items():
            if frag in username.lower():
                host, port = h, p
                break
    return host, port, username, password, sender_name


def send_email(to_email: str, subject: str, body: str,
               is_html: bool = True, settings_obj=None) -> bool:
    """Send an email. Returns True on success (or mock), False on failure."""
    if not to_email:
        logger.warning("send_email called with no recipient; skipping")
        return False

    host, port, username, password, sender_name = _resolve_smtp(settings_obj)

    if not password or username == "dummy@example.com":
        logger.info("[MOCK EMAIL] to=%s subject=%s (no SMTP configured)", to_email, subject)
        return True

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{sender_name} <{username}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html" if is_html else "plain"))

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception as e:
        logger.exception("Failed to send email to %s: %s", to_email, e)
        return False


# ---------------------------------------------------------------------------
# HTML shell + helpers
# ---------------------------------------------------------------------------
def get_base_html(title: str, content: str, company_name: str = "HiringBuddy",
                  accent: str = BRAND) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0b0713;font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0b0713;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;width:100%;background:#14101f;border-radius:20px;overflow:hidden;border:1px solid #2a2140;">
        <tr><td style="background:linear-gradient(135deg,{accent},{BRAND_2});padding:28px 32px;">
          <span style="color:#fff;font-size:22px;font-weight:800;letter-spacing:-0.5px;">⚡ {company_name}</span>
        </td></tr>
        <tr><td style="padding:36px 32px 8px;">
          <h1 style="margin:0 0 18px;color:#ffffff;font-size:24px;font-weight:700;">{title}</h1>
          <div style="color:#c7c2d6;font-size:15px;line-height:1.7;">{content}</div>
        </td></tr>
        <tr><td style="padding:24px 32px 32px;">
          <div style="border-top:1px solid #2a2140;padding-top:18px;color:#6f6785;font-size:12px;line-height:1.5;">
            This is an automated message from {company_name}. Please do not reply directly to this email.
          </div>
        </td></tr>
      </table>
      <div style="color:#4a4458;font-size:11px;margin-top:16px;">Powered by HiringBuddy AI Recruitment Platform</div>
    </td></tr>
  </table>
</body>
</html>"""


def _button(label: str, url: str, accent: str = BRAND) -> str:
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:22px 0;"><tr><td '
            f'style="border-radius:12px;background:linear-gradient(135deg,{accent},{BRAND_2});">'
            f'<a href="{url}" style="display:inline-block;padding:14px 28px;color:#fff;font-weight:700;'
            f'font-size:15px;text-decoration:none;border-radius:12px;">{label}</a></td></tr></table>')


def _info_box(rows: dict, accent: str = BRAND) -> str:
    items = "".join(
        f'<tr><td style="padding:6px 0;color:#8b849c;font-size:13px;width:130px;">{k}</td>'
        f'<td style="padding:6px 0;color:#eae7f2;font-size:14px;font-weight:600;">{v}</td></tr>'
        for k, v in rows.items()
    )
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="background:#1c1630;border:1px solid {accent}55;border-radius:14px;padding:16px 20px;margin:20px 0;">'
            f'{items}</table>')


def render_template(template: str, context: dict) -> str:
    """Render an HR-editable {{token}} plain-text template into HTML paragraphs."""
    result = template
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    html = result.replace("\n\n", "</p><p style='margin:0 0 14px;'>").replace("\n", "<br>")
    return f"<p style='margin:0 0 14px;'>{html}</p>"


def _ctx(settings_obj, name, role, **extra):
    company = (settings_obj.company_name if settings_obj and settings_obj.company_name else "HiringBuddy")
    hr = (settings_obj.sender_name if settings_obj and settings_obj.sender_name else "The Hiring Team")
    return {"candidate_name": name, "job_role": role, "company_name": company, "hr_name": hr, **extra}


# ---------------------------------------------------------------------------
# Typed senders
# ---------------------------------------------------------------------------
def send_invite_email(candidate_email, name, date, time, link,
                      settings_obj=None, role="Software Engineer") -> bool:
    c = _ctx(settings_obj, name, role)
    tmpl = settings_obj.invite_template if settings_obj else None
    if tmpl:
        content = render_template(tmpl, {**c, "interview_date": date, "interview_time": time,
                                         "interview_link": _button("Join Interview", link)})
    else:
        content = f"""<p>Dear {name},</p>
        <p>Congratulations! You are invited to an interview for the <strong>{role}</strong> position at {c['company_name']}.</p>
        {_info_box({'Date': date or 'To be scheduled', 'Time': time or 'To be scheduled', 'Format': 'AI-assisted video interview'})}
        <p>Click below to join when you're ready. Please use a laptop with a working webcam and microphone.</p>
        {_button('Join Interview', link)}
        <p style="color:#8b849c;font-size:13px;">If the button doesn't work, copy this link:<br>{link}</p>
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, "Your Interview Invitation", get_base_html("You're Invited to Interview 🎯", content, c["company_name"]), True, settings_obj)


def send_shortlist_email(candidate_email, name, settings_obj=None, role="Software Engineer") -> bool:
    c = _ctx(settings_obj, name, role)
    tmpl = settings_obj.shortlist_template if settings_obj else None
    content = render_template(tmpl, c) if tmpl else f"""<p>Dear {name},</p>
        <p>Great news — you've been <strong>shortlisted</strong> for the {role} position at {c['company_name']}!</p>
        <p>Our team was impressed with your background and skills. We'll be in touch shortly with next steps.</p>
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, "You've Been Shortlisted! 🎉", get_base_html("Application Shortlisted", content, c["company_name"], "#16a34a"), True, settings_obj)


def send_reject_email(candidate_email, name, settings_obj=None, role="Software Engineer") -> bool:
    c = _ctx(settings_obj, name, role)
    tmpl = settings_obj.reject_template if settings_obj else None
    content = render_template(tmpl, c) if tmpl else f"""<p>Dear {name},</p>
        <p>Thank you for applying for the {role} position at {c['company_name']} and for the time you invested.</p>
        <p>After careful consideration, we've decided to move forward with other candidates whose profiles more closely match the role at this time.</p>
        <p>We genuinely appreciate your interest and wish you the very best in your search.</p>
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, "Update on Your Application", get_base_html("Application Update", content, c["company_name"], "#ef4444"), True, settings_obj)


def send_offer_email(candidate_email, name, settings_obj=None, role="Software Engineer",
                     salary="", start_date="", link="") -> bool:
    c = _ctx(settings_obj, name, role)
    box = {"Position": role}
    if salary:
        box["Compensation"] = salary
    if start_date:
        box["Start Date"] = start_date
    action = _button("View Offer Letter", link, "#16a34a") if link else ""
    content = f"""<p>Dear {name},</p>
        <p>We're delighted to extend an <strong>offer</strong> for the {role} position at {c['company_name']}!</p>
        {_info_box(box, '#16a34a')}
        <p>We were thoroughly impressed throughout the process and can't wait to have you on the team.</p>
        {action}
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, f"Job Offer — {role}", get_base_html("Congratulations! 🎊", content, c["company_name"], "#16a34a"), True, settings_obj)


def send_reminder_email(candidate_email, name, date, time, link,
                        settings_obj=None, role="Software Engineer") -> bool:
    c = _ctx(settings_obj, name, role)
    content = f"""<p>Dear {name},</p>
        <p>A friendly reminder about your upcoming interview for the {role} position at {c['company_name']}.</p>
        {_info_box({'Date': date or 'As scheduled', 'Time': time or 'As scheduled'})}
        <p>Please join a few minutes early and check your camera and microphone.</p>
        {_button('Join Interview', link)}
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, "Reminder: Your Upcoming Interview", get_base_html("Interview Reminder ⏰", content, c["company_name"], "#f59e0b"), True, settings_obj)


def send_confirmation_email(candidate_email, name, date, time,
                            settings_obj=None, role="Software Engineer") -> bool:
    c = _ctx(settings_obj, name, role)
    content = f"""<p>Dear {name},</p>
        <p>This confirms your interview for the {role} position at {c['company_name']} has been scheduled.</p>
        {_info_box({'Date': date or 'As scheduled', 'Time': time or 'As scheduled', 'Status': 'Confirmed ✓'}, '#16a34a')}
        <p>We look forward to speaking with you. You'll receive a reminder before the session.</p>
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, "Interview Confirmed", get_base_html("Interview Confirmation ✅", content, c["company_name"], "#16a34a"), True, settings_obj)


def send_reschedule_email(candidate_email, name, date, time, link,
                          settings_obj=None, role="Software Engineer") -> bool:
    c = _ctx(settings_obj, name, role)
    content = f"""<p>Dear {name},</p>
        <p>Your interview for the {role} position at {c['company_name']} has been <strong>rescheduled</strong>.</p>
        {_info_box({'New Date': date or 'To be confirmed', 'New Time': time or 'To be confirmed'}, '#f59e0b')}
        <p>Please use the same link below to join at the new time.</p>
        {_button('Join Interview', link)}
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, "Your Interview Has Been Rescheduled", get_base_html("Interview Rescheduled 🗓️", content, c["company_name"], "#f59e0b"), True, settings_obj)


def send_welcome_email(candidate_email, name, settings_obj=None, role="Software Engineer", start_date="") -> bool:
    c = _ctx(settings_obj, name, role)
    content = f"""<p>Dear {name},</p>
        <p>Welcome to {c['company_name']}! We're thrilled to have you join us as a <strong>{role}</strong>.</p>
        {_info_box({'Role': role, 'Start Date': start_date or 'To be confirmed'}, '#16a34a')}
        <p>Your onboarding details will follow shortly. We can't wait to see the impact you'll make.</p>
        <p>Warm regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, f"Welcome to {c['company_name']}!", get_base_html("Welcome Aboard 🎉", content, c["company_name"], "#16a34a"), True, settings_obj)


def send_followup_email(candidate_email, name, settings_obj=None, role="Software Engineer", message="") -> bool:
    c = _ctx(settings_obj, name, role)
    body = message or (
        f"We wanted to follow up regarding your application for the {role} position — "
        "it's still under active review, and we'll be in touch with an update soon."
    )
    content = f"""<p>Dear {name},</p>
        <p>{body}</p>
        <p>Thank you for your patience and continued interest in {c['company_name']}.</p>
        <p>Best regards,<br><strong>{c['hr_name']}</strong><br>{c['company_name']}</p>"""
    return send_email(candidate_email, "Following Up on Your Application", get_base_html("A Quick Update 👋", content, c["company_name"]), True, settings_obj)
