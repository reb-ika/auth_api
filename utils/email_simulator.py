import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_send_email(email: str, code: str):
    """Simulate sending email with verification code"""
    logger.info(f"""
    ========================================
    EMAIL SIMULATION
    To: {email}
    Subject: Email Verification Code
    
    Your verification code is: {code}
    This code will expire in 10 minutes.
    
    Timestamp: {datetime.now()}
    ========================================
    """)
    # In production, you would integrate with SendGrid, AWS SES, etc.
    return True