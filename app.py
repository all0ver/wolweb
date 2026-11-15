from flask import Flask, jsonify, render_template_string, request
import subprocess, json, re

app = Flask(__name__)
DEVICES_FILE = '/etc/wolweb/devices.json'


def load_devices():
    with open(DEVICES_FILE) as f:
        return json.load(f)['devices']


def save_devices(devices):
    with open(DEVICES_FILE, 'w') as f:
        json.dump({"devices": devices}, f, indent=2)


def valid_mac(mac):
    return bool(re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', mac))


HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Wake on LAN</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light">
<div class="container py-5">

    <div class="d-flex justify-content-between align-items-start mb-4">
        <div>
            <h1 class="mb-0">&#9889; Wake on LAN</h1>
            <p class="text-secondary mb-0 small">rpi4 &middot; 192.168.33.200</p>
        </div>
        <button class="btn btn-outline-success" onclick="openModal()">+ Dodaj</button>
    </div>

    <div class="row g-3">
    {% for d in devices %}
        <div class="col-sm-6 col-md-4">
            <div class="card bg-secondary border-0 h-100">
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">{{ d.name }}</h5>
                    <p class="text-muted small mb-3 font-monospace">{{ d.mac }}</p>
                    <div class="d-flex gap-2 mt-auto">
                        <button class="btn btn-success flex-grow-1"
                                onclick="wake('{{ d.mac }}', this)">Wake</button>
                        <button class="btn btn-outline-light" title="Edytuj"
                                onclick="openModal('{{ d.name }}', '{{ d.mac }}')">&#9998;</button>
                        <button class="btn btn-outline-danger" title="Usuń"
                                onclick="openDeleteModal('{{ d.name }}', '{{ d.mac }}')">&#128465;</button>
                    </div>
                </div>
            </div>
        </div>
    {% endfor %}
    </div>
</div>

<!-- Add/Edit Modal -->
<div class="modal fade" id="deviceModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content bg-dark border-secondary">
            <div class="modal-header border-secondary">
                <h5 class="modal-title" id="modalTitle">Dodaj urządzenie</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="mb-3">
                    <label class="form-label">Nazwa</label>
                    <input type="text" class="form-control bg-secondary text-light border-secondary"
                           id="inputName" placeholder="np. Desktop">
                </div>
                <div class="mb-3">
                    <label class="form-label">Adres MAC</label>
                    <input type="text" class="form-control bg-secondary text-light border-secondary font-monospace"
                           id="inputMac" placeholder="AA:BB:CC:DD:EE:FF" maxlength="17">
                </div>
                <div id="modalError" class="alert alert-danger d-none py-2 mb-0"></div>
            </div>
            <div class="modal-footer border-secondary">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
                <button type="button" class="btn btn-success" onclick="saveDevice()">Zapisz</button>
            </div>
        </div>
    </div>
</div>

<!-- Delete Modal -->
<div class="modal fade" id="deleteModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content bg-dark border-secondary">
            <div class="modal-header border-secondary">
                <h5 class="modal-title">Usuń urządzenie</h5>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                Na pewno usunąć <strong id="deleteDeviceName"></strong>?
            </div>
            <div class="modal-footer border-secondary">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
                <button type="button" class="btn btn-danger" onclick="confirmDelete()">Usuń</button>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
let editingMac = null;
let pendingDeleteMac = null;
const deviceModal = new bootstrap.Modal(document.getElementById('deviceModal'));
const deleteModal  = new bootstrap.Modal(document.getElementById('deleteModal'));

// Auto-format MAC address while typing
document.getElementById('inputMac').addEventListener('input', function () {
    let raw = this.value.replace(/[^0-9a-fA-F]/g, '').toUpperCase().substring(0, 12);
    let formatted = '';
    for (let i = 0; i < raw.length; i++) {
        if (i > 0 && i % 2 === 0) formatted += ':';
        formatted += raw[i];
    }
    this.value = formatted;
});

function openModal(name = '', mac = '') {
    editingMac = mac || null;
    document.getElementById('modalTitle').textContent = mac ? 'Edytuj urządzenie' : 'Dodaj urządzenie';
    document.getElementById('inputName').value = name;
    document.getElementById('inputMac').value = mac;
    document.getElementById('modalError').classList.add('d-none');
    deviceModal.show();
    setTimeout(() => document.getElementById('inputName').focus(), 300);
}

function openDeleteModal(name, mac) {
    pendingDeleteMac = mac;
    document.getElementById('deleteDeviceName').textContent = name;
    deleteModal.show();
}

async function saveDevice() {
    const name    = document.getElementById('inputName').value.trim();
    const mac     = document.getElementById('inputMac').value.trim();
    const errorEl = document.getElementById('modalError');

    if (!name || !mac) {
        errorEl.textContent = 'Wypełnij wszystkie pola.';
        errorEl.classList.remove('d-none');
        return;
    }

    const url    = editingMac ? `/devices/${encodeURIComponent(editingMac)}` : '/devices';
    const method = editingMac ? 'PUT' : 'POST';

    const r    = await fetch(url, { method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name, mac}) });
    const data = await r.json();

    if (data.status === 'ok') { deviceModal.hide(); window.location.reload(); }
    else { errorEl.textContent = data.msg || 'Błąd serwera'; errorEl.classList.remove('d-none'); }
}

async function confirmDelete() {
    const r    = await fetch(`/devices/${encodeURIComponent(pendingDeleteMac)}`, {method: 'DELETE'});
    const data = await r.json();
    if (data.status === 'ok') { deleteModal.hide(); window.location.reload(); }
}

function wake(mac, btn) {
    const orig = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Wysyłam...';
    fetch('/wake/' + encodeURIComponent(mac)).then(r => r.json()).then(() => {
        btn.textContent = '\u2705 Wysłano!';
        btn.classList.replace('btn-success', 'btn-primary');
        setTimeout(() => { btn.disabled = false; btn.textContent = orig; btn.classList.replace('btn-primary', 'btn-success'); }, 3000);
    });
}
</script>
</body>
</html>"""


@app.route('/')
def index():
    return render_template_string(HTML, devices=load_devices())


@app.route('/wake/<mac>')
def wake(mac):
    if not valid_mac(mac):
        return jsonify({"status": "error", "msg": "Nieprawidłowy MAC"}), 400
    if mac not in [d['mac'] for d in load_devices()]:
        return jsonify({"status": "error", "msg": "Nieznane urządzenie"}), 404
    subprocess.run(['wakeonlan', mac])
    return jsonify({"status": "sent"})


@app.route('/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    name = (data.get('name') or '').strip()
    mac  = (data.get('mac')  or '').strip().upper()
    if not name or not valid_mac(mac):
        return jsonify({"status": "error", "msg": "Nieprawidłowe dane"}), 400
    devices = load_devices()
    if any(d['mac'].upper() == mac for d in devices):
        return jsonify({"status": "error", "msg": "Urządzenie już istnieje"}), 409
    devices.append({"name": name, "mac": mac})
    save_devices(devices)
    return jsonify({"status": "ok"})


@app.route('/devices/<original_mac>', methods=['PUT'])
def edit_device(original_mac):
    data = request.get_json()
    name = (data.get('name') or '').strip()
    mac  = (data.get('mac')  or '').strip().upper()
    if not name or not valid_mac(mac):
        return jsonify({"status": "error", "msg": "Nieprawidłowe dane"}), 400
    devices = load_devices()
    for d in devices:
        if d['mac'].upper() == original_mac.upper():
            d['name'] = name
            d['mac']  = mac
            save_devices(devices)
            return jsonify({"status": "ok"})
    return jsonify({"status": "error", "msg": "Nie znaleziono"}), 404


@app.route('/devices/<mac>', methods=['DELETE'])
def delete_device(mac):
    devices     = load_devices()
    new_devices = [d for d in devices if d['mac'].upper() != mac.upper()]
    if len(new_devices) == len(devices):
        return jsonify({"status": "error", "msg": "Nie znaleziono"}), 404
    save_devices(new_devices)
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8089)
