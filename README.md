# AD Account Unlock via OTP — FastAPI App

Self-service Active Directory account unlock using OTP via SMS, WhatsApp, and Email.

## Project Structure

```
ad_otp_unlock/
├── main.py                          # FastAPI app entry point
├── config.py                        # Settings from .env
├── database.py                      # SQLAlchemy models + DB init
├── requirements.txt
├── .env.example                     # Copy to .env and fill values
├── routers/
│   ├── auth.py                      # POST /api/auth/request-otp
│   ├── unlock.py                    # POST /api/unlock/verify
│   └── admin.py                     # GET  /api/admin/logs|stats
└── services/
    ├── otp_service.py               # OTP generate / hash / validate
    ├── notification_service.py      # SMS + WhatsApp + Email sender
    ├── ad_service.py                # LDAP / Graph API AD integration
    └── risk_engine.py               # IP check + attempt frequency
```

## Setup

```bash
# 1. Clone / copy files
cd ad_otp_unlock

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your AD server, Twilio, SendGrid credentials

# 5. Run
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Step 1 — Request OTP
```http
POST /api/auth/request-otp
Content-Type: application/json

{
  "username": "john.doe",
  "preferred_channel": "sms"   // sms | whatsapp | email
}
```
Response:
```json
{
  "success": true,
  "message": "OTP sent successfully via sms.",
  "channel": "sms",
  "masked_contact": "****9876"
}
```

### Step 2 — Verify OTP & Unlock
```http
POST /api/unlock/verify
Content-Type: application/json

{
  "username": "john.doe",
  "otp": "483920"
}
```
Response:
```json
{
  "success": true,
  "message": "Your account has been successfully unlocked."
}
```

### Admin — Audit Logs
```http
GET /api/admin/logs?username=john.doe&limit=20
GET /api/admin/stats
```

## AD Integration Notes

In Demo Mode, this project uses a fake in-memory user database and does not require LDAP or Microsoft Graph.

**Demo users:**
- john (locked: true)
- yuva (locked: false)
- rajasekar (locked: true)

**On-premise AD (LDAP):** Fill `AD_SERVER`, `AD_BIND_USER`, `AD_BIND_PASSWORD`, `AD_BASE_DN`.  
**Azure AD / Hybrid:** Fill `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET`. The app auto-selects Graph API when these are set.  
**Windows only:** The PowerShell fallback (`Unlock-ADAccount`) runs if LDAP fails. Requires RSAT tools installed.

## Security Notes

- OTPs are bcrypt-hashed before storage — never stored in plain text
- Each OTP expires in 5 minutes (configurable)
- Max 3 attempts per OTP before lockout
- Risk engine auto-escalates high-risk requests to IT helpdesk
- Admin endpoints should be restricted to internal IPs / VPN only
- Use PostgreSQL in production, not SQLite

## Interactive Docs

Visit `http://localhost:8000/docs` for the Swagger UI once the app is running.
