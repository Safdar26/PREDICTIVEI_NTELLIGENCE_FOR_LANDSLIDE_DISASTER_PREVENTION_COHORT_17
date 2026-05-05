from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

from database import get_db
import models, security
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str

# Token validation dependency
def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def generate_otp():
    return str(random.randint(100000, 999999))

def build_otp_html(otp_code: str, expire_minutes: int) -> str:
    """Returns a premium HTML email body for OTP verification."""
    digits = list(otp_code)
    digit_boxes = "".join([
        f'<td style="width:52px;height:64px;background:#1e293b;border:2px solid #3b82f6;border-radius:12px;'
        f'text-align:center;vertical-align:middle;font-size:32px;font-weight:800;color:#60a5fa;'
        f'font-family:monospace;letter-spacing:0;padding:0 4px;">{d}</td>'
        f'<td style="width:8px;"></td>'
        for d in digits
    ])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>GeoPredict Verification</title>
</head>
<body style="margin:0;padding:0;background:#020617;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#020617;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">

          <!-- Header -->
          <tr>
            <td align="center" style="padding-bottom:32px;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:linear-gradient(135deg,#1d4ed8,#4f46e5);border-radius:16px;padding:12px 28px;">
                    <span style="font-size:22px;font-weight:900;color:#fff;letter-spacing:-0.5px;">&#127760; GeoPredict</span>
                    <span style="font-size:11px;color:#93c5fd;display:block;text-align:center;letter-spacing:3px;margin-top:2px;">EARLY WARNING SYSTEM</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Card -->
          <tr>
            <td style="background:linear-gradient(160deg,#0f172a 0%,#1e293b 100%);border-radius:24px;border:1px solid #1e3a5f;overflow:hidden;">

              <!-- Top accent bar -->
              <tr>
                <td style="height:4px;background:linear-gradient(90deg,#1d4ed8,#7c3aed,#06b6d4);"></td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:48px 48px 40px;">

                  <!-- Icon -->
                  <table cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
                    <tr>
                      <td style="background:rgba(59,130,246,0.15);border:1px solid rgba(59,130,246,0.3);border-radius:16px;padding:16px;width:56px;height:56px;text-align:center;vertical-align:middle;">
                        <span style="font-size:28px;">&#128274;</span>
                      </td>
                    </tr>
                  </table>

                  <!-- Title -->
                  <p style="margin:0 0 8px;font-size:28px;font-weight:800;color:#f1f5f9;line-height:1.2;">Verify Your Account</p>
                  <p style="margin:0 0 32px;font-size:15px;color:#94a3b8;line-height:1.6;">
                    Welcome to GeoPredict! Enter the verification code below to activate your account and gain access to the AI-powered landslide early warning dashboard.
                  </p>

                  <!-- OTP Digit Boxes -->
                  <table cellpadding="0" cellspacing="0" style="margin:0 0 32px;">
                    <tr>
                      {digit_boxes}
                    </tr>
                  </table>

                  <!-- Expiry notice -->
                  <table cellpadding="0" cellspacing="0" style="margin-bottom:36px;">
                    <tr>
                      <td style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:10px;padding:12px 16px;">
                        <span style="font-size:13px;color:#fbbf24;">&#9203; </span>
                        <span style="font-size:13px;color:#fcd34d;font-weight:600;">This code expires in {expire_minutes} minutes.</span>
                        <span style="font-size:13px;color:#94a3b8;"> Do not share it with anyone.</span>
                      </td>
                    </tr>
                  </table>

                  <!-- Divider -->
                  <hr style="border:none;border-top:1px solid #1e3a5f;margin:0 0 28px;" />

                  <!-- Security note -->
                  <p style="margin:0;font-size:13px;color:#64748b;line-height:1.7;">
                    &#128737; If you did not create a GeoPredict account, you can safely ignore this email.
                    Someone may have entered your email address by mistake.
                  </p>

                </td>
              </tr>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="padding-top:28px;">
              <p style="margin:0 0 6px;font-size:13px;color:#334155;">GeoPredict &mdash; Predictive Intelligence for Landslide Disaster Prevention</p>
              <p style="margin:0;font-size:12px;color:#1e3a5f;">&#169; 2025 GeoPredict. All rights reserved.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

def send_otp_email(to_email: str, otp_code: str):
    """Sends OTP via SMTP with a rich HTML template. Falls back to console print."""
    smtp_pwd  = os.getenv("SMTP_PASSWORD", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    expire_minutes = security.OTP_EXPIRE_MINUTES

    if smtp_pwd and smtp_pwd != "your_app_password" and smtp_user:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "🔐 GeoPredict — Your Verification Code"
            msg["From"]    = f"GeoPredict EWS <{smtp_user}>"
            msg["To"]      = to_email

            # Plain-text fallback
            plain = (
                f"Your GeoPredict verification code is: {otp_code}\n"
                f"Valid for {expire_minutes} minutes. Do not share this code."
            )
            msg.attach(MIMEText(plain, "plain"))

            # Rich HTML version
            html_body = build_otp_html(otp_code, expire_minutes)
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pwd)
                server.sendmail(smtp_user, to_email, msg.as_string())

            logger.info(f"OTP email sent successfully to {to_email}")

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP Authentication failed! Your Gmail App Password is incorrect or not set.\n"
                "Fix: Go to myaccount.google.com → Security → 2-Step Verification → App passwords\n"
                f"Then update SMTP_PASSWORD in backend/.env"
            )
            # Still print OTP to console so dev work isn't blocked
            _print_otp_console(to_email, otp_code, expire_minutes)
        except Exception as e:
            logger.error(f"Failed to send OTP email to {to_email}: {e}")
            _print_otp_console(to_email, otp_code, expire_minutes)
    else:
        logger.warning(
            "SMTP_PASSWORD not configured in .env — printing OTP to console.\n"
            "To enable real emails, add your Gmail App Password to SMTP_PASSWORD in backend/.env"
        )
        _print_otp_console(to_email, otp_code, expire_minutes)

def _print_otp_console(to_email: str, otp_code: str, expire_minutes: int):
    print(f"\n{'='*50}")
    print(f"  📧  SIMULATED OTP EMAIL")
    print(f"{'='*50}")
    print(f"  To:      {to_email}")
    print(f"  Code:    {otp_code}")
    print(f"  Expires: {expire_minutes} minutes")
    print(f"{'='*50}\n")


def build_disaster_alert_html(location: str, category: str, risk_score: float, rainfall: float, terrain: str):
    """
    Constructs a premium HTML email template for Landslide Disaster Alerts.
    The theme adjusts based on CRITICAL EVACUATION vs WARNING.
    """
    theme_color = "#e11d48" if category == "CRITICAL EVACUATION" else "#f97316"
    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background-color:#0f172a;font-family:'Segoe UI',Roboto,sans-serif;color:#e2e8f0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-w-width:600px;margin:auto;background-color:#1e293b;border-radius:12px;overflow:hidden;border:1px solid #334155;">
    <tr>
      <td style="padding:30px;text-align:center;background-color:#0f172a;border-bottom:3px solid {theme_color};">
        <h1 style="color:#f8fafc;margin:0;font-size:24px;letter-spacing:1px;">🚨 GeoPredict Early Warning</h1>
        <p style="color:{theme_color};margin:10px 0 0 0;font-weight:bold;letter-spacing:2px;font-size:14px;">AUTOMATED DISASTER DISPATCH</p>
      </td>
    </tr>
    <tr>
      <td style="padding:30px;">
        <h2 style="color:{theme_color};margin:0 0 15px 0;">{category}</h2>
        <p style="font-size:16px;line-height:1.5;">You are receiving this automated alert because a region you are tracking has crossed critical danger thresholds for landslide susceptibility.</p>
        
        <table width="100%" style="margin-top:20px;background-color:#0f172a;border-radius:8px;padding:15px;border:1px solid #334155;">
          <tr>
            <td style="padding:8px 0;color:#94a3b8;font-size:14px;"><strong>Location:</strong></td>
            <td style="padding:8px 0;color:#f8fafc;font-size:14px;">{location}</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#94a3b8;font-size:14px;"><strong>Risk Score:</strong></td>
            <td style="padding:8px 0;color:{theme_color};font-size:16px;font-weight:bold;">{risk_score} / 100</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#94a3b8;font-size:14px;"><strong>1h Rainfall:</strong></td>
            <td style="padding:8px 0;color:#38bdf8;font-size:14px;">{rainfall} mm</td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#94a3b8;font-size:14px;"><strong>Terrain Profile:</strong></td>
            <td style="padding:8px 0;color:#fadd8;font-size:14px;">{terrain}</td>
          </tr>
        </table>
        
        <p style="margin-top:25px;font-size:14px;color:#cbd5e1;line-height:1.5;">
          <strong>ACTION REQUIRED:</strong> Please advise local authorities or evacuate immediately if situated in low-lying structural zones or beneath steep slopes. Heavy rainfall combined with high subsurface saturation severely destabilizes {terrain}.
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding:20px;text-align:center;background-color:#0f172a;border-top:1px solid #334155;">
        <p style="margin:0;font-size:12px;color:#64748b;">Powered by NASA LHASA & OpenWeather API</p>
        <p style="margin:5px 0 0 0;font-size:11px;color:#475569;">Do not reply to this automated dispatch.</p>
      </td>
    </tr>
  </table>
</body>
</html>"""

def send_disaster_alert_email(to_email: str, location: str, category: str, risk_score: float, rainfall: float, terrain: str):
    """Sends a formatted Mass Casualty / Disaster Alert Email via SMTP."""
    smtp_pwd  = os.getenv("SMTP_PASSWORD", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if smtp_pwd and smtp_pwd != "your_app_password" and smtp_user:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{category}] GeoPredict Alert: {location}"
            msg["From"]    = f"GeoPredict EWS <{smtp_user}>"
            msg["To"]      = to_email

            plain = (
                f"🚨 {category} 🚨\n\n"
                f"Location: {location}\n"
                f"Risk Score: {risk_score}/100\n"
                f"Rainfall (1h): {rainfall}mm\n"
                f"Terrain: {terrain}\n\n"
                f"Please take extreme caution or evacuate if necessary. Powered by NASA."
            )
            msg.attach(MIMEText(plain, "plain"))

            html_body = build_disaster_alert_html(location, category, risk_score, rainfall, terrain)
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pwd)
                server.sendmail(smtp_user, to_email, msg.as_string())

            logger.info(f"🚨 Disaster Alert successfully dispatched to {to_email} for {location}")
        except Exception as e:
            logger.error(f"Failed to send disaster alert email to {to_email}: {e}")
    else:
        logger.warning(f"Could not dispatch disaster alert to {to_email}. SMTP not configured.")



@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pass = security.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pass, is_active=True)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize empty profile
    profile_entry = models.Profile(user_id=new_user.id)
    db.add(profile_entry)
    db.commit()

    return {"message": "User registered successfully. You can now login.", "email": new_user.email}



@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email, "is_admin": user.is_admin}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin}

@router.get("/me")
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "is_admin": current_user.is_admin, "is_active": current_user.is_active}
