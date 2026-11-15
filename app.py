from flask import Flask, jsonify, render_template_string
import subprocess, json

app = Flask(__name__)
DEVICES_FILE = '/etc/wolweb/devices.json'

def load_devices():
    with open(DEVICES_FILE) as f:
        return json.load(f)['devices']

HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Wake on LAN</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light">
<div class="container py-5">
    <h1 class="mb-1">&#9889; Wake on LAN</h1>
    <p class="text-secondary mb-4">rpi4 &middot; 192.168.33.200</p>
    <div class="row g-3">
    {% for d in devices %}
        <div class="col-sm-6 col-md-4">
            <div class="card bg-secondary border-0 h-100">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">{{ d.name }}</h5>
                    <p class="text-muted small mb-3">{{ d.mac }}</p>
                    <button class="btn btn-success mt-auto"
                            onclick="wake('{{ d.mac }}', this)">
                        Wake
                    </button>
                </div>
            </div>
        </div>
    {% endfor %}
    </div>
</div>
<script>
function wake(mac, btn) {
    const orig = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Wysyłam...';
    fetch('/wake/' + mac).then(r => r.json()).then(() => {
        btn.textContent = '\u2705 Wysłano!';
        btn.classList.replace('btn-success','btn-primary');
        setTimeout(() => {
            btn.disabled = false;
            btn.textContent = orig;
            btn.classList.replace('btn-primary','btn-success');
        }, 3000);
    });
}
</script>
</body>
</html>"""

ALLOWED_CHARS = set('0123456789abcdefABCDEF:')

@app.route('/')
def index():
    return render_template_string(HTML, devices=load_devices())

@app.route('/wake/<mac>')
def wake(mac):
    if not all(c in ALLOWED_CHARS for c in mac):
        return jsonify({"status": "error", "msg": "nieprawidłowy MAC"}), 400
    known = [d['mac'] for d in load_devices()]
    if mac not in known:
        return jsonify({"status": "error", "msg": "nieznane urządzenie"}), 404
    subprocess.run(['wakeonlan', mac])
    return jsonify({"status": "sent"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8089)
