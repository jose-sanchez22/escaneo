from flask import Flask, render_template_string, jsonify, send_file, request
from markupsafe import escape
import random
import os
from datetime import datetime

app = Flask(__name__)

# --- Datos base ---
NODOS = {
    "PC_Docker_1": "10.0.0.11",
    "PC_Docker_2": "10.0.0.12",
    "DNS_NTP": "10.0.20.10",
    "Grafana": "10.0.40.10"
}

# Historial y métricas (datos ficticios)
historico_nodos = {nombre: [random.randint(50, 100) for _ in range(20)] for nombre in NODOS}
trafico_red = [{"Nodo": k, "Enviado": random.randint(100, 1000), "Recibido": random.randint(200, 1500)} for k in NODOS]
historial_comandos = [
    {
        'hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'nodo': 'PC_Docker_1',
        'comando': 'ipconfig /all',
        'salida': 'Windows IP Configuration\n   Host Name: PC_Docker_1\n   IP Address: 10.0.0.11'
    },
    {
        'hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'nodo': 'DNS_NTP',
        'comando': 'ping -c 4',
        'salida': 'PING 10.0.20.10 (10.0.20.10): 56 data bytes\n64 bytes from 10.0.20.10: icmp_seq=0 ttl=64 time=0.123 ms'
    }
]

# --- Función de ping simulado ---
def ping_node(ip):
    return random.choice([True, True, True, False])

# --- Plantillas HTML completas ---
HTML_HOME = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Dashboard Interactivo</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body { margin: 0; padding: 2rem; font-family: 'Segoe UI'; background: linear-gradient(135deg, #0f2027, #203a43, #2c5364); color: #eee; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }
  h1 { font-size: 3.5rem; margin-bottom: 2rem; text-shadow: 0 0 15px #00ffe7; }
  .btn { background: linear-gradient(135deg, #00ffc8, #0052d4); border: none; color: #fff; padding: 1rem 3rem; margin: 1rem; font-size: 1.4rem; font-weight: 700; border-radius: 12px; box-shadow: 0 0 15px #00ffc8; cursor: pointer; text-decoration: none; display: inline-block; transition: transform .3s, box-shadow .3s; }
  .btn:hover { transform: scale(1.1); box-shadow: 0 0 30px #00ffe7; }
  footer { margin-top: auto; font-size: .9rem; color: #888; user-select: none; }
</style>
</head>
<body>
  <h1>🖥️ Dashboard Interactivo</h1>
  <a href="/nodos" class="btn">📡 Estado de Nodos</a>
  <a href="/graficas" class="btn">📈 Gráficas Dinámicas</a>
  <a href="/trafico" class="btn">📊 Tráfico de Red</a>
  <a href="/topologia" class="btn">🗺️ Topología</a>
  <a href="/comandos" class="btn">💻 Ejecutar Comandos</a>
  <a href="/nmap" class="btn">🛡️ Escaneo Nmap</a>
  <a href="/historial" class="btn">📜 Historial</a>
  <footer>Creado por tu asistente 🤖</footer>
</body>
</html>
'''

HTML_NODOS = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Estado de Nodos</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body { background: #121212; color: #00ffe7; font-family: 'Segoe UI'; margin: 0; padding: 2rem; display: flex; flex-direction: column; align-items: center; }
  h1 { font-size: 2.8rem; margin-bottom: 1.5rem; text-shadow: 0 0 10px #00ffe7; }
  #nodos { width: 100%; max-width: 500px; background: #222; border-radius: 15px; box-shadow: 0 0 20px #00ffe7aa; padding: 1.5rem; font-size: 1.3rem; }
  p { margin: .8rem 0; display: flex; justify-content: space-between; border-bottom: 1px solid #00ffe755; padding-bottom: .4rem; transition: background .4s; cursor: default; }
  p:hover { background: #00ffe733; }
  .ok { color: #00ff88; font-weight: 700; }
  .fail { color: #ff4444; font-weight: 700; }
  a.btn-back { margin-top: 2rem; color: #00ffe7; text-decoration: none; font-weight: 600; font-size: 1.2rem; }
  a.btn-back:hover { text-decoration: underline; }
</style>
</head>
<body>
  <h1>📡 Estado de los Nodos</h1>
  <div id="nodos"></div>
  <a href="/" class="btn-back">⬅️ Volver al Inicio</a>
<script>
async function cargar() {
  let res = await fetch('/estado-json');
  let data = await res.json();
  const cont = document.getElementById('nodos');
  cont.innerHTML = '';
  Object.entries(data).forEach(([k,v]) => {
    const p = document.createElement('p');
    p.innerHTML = `<span>${k.replace('_',' ')}</span><span class="${v?'ok':'fail'}">${v?'✅ ONLINE':'❌ OFFLINE'}</span>`;
    cont.appendChild(p);
  });
}
cargar();
setInterval(cargar, 10000);
</script>
</body>
</html>
'''

HTML_GRAFICAS = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Gráficas Dinámicas</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  body { background: #121212; color: #00ffe7; font-family: 'Segoe UI'; margin: 0; padding: 2rem; text-align: center; }
  h1 { font-size: 2.8rem; margin-bottom: 1.5rem; text-shadow: 0 0 10px #00ffe7; }
  .grafica { display: inline-block; margin: 1rem; background: #222; padding: 1rem; border-radius: 15px; box-shadow: 0 0 20px #00ffe7aa; }
  .grafica h3 { margin: 0 0 .8rem; font-weight: 700; }
  canvas { max-width: 320px; max-height: 180px; }
  a.btn-back { display: inline-block; margin-top: 2rem; color: #00ffe7; text-decoration: none; font-weight: 600; font-size: 1.2rem; }
  a.btn-back:hover { text-decoration: underline; }
</style>
</head>
<body>
  <h1>📈 Actividad por Nodo</h1>
  {% for nodo in nodos %}
    <div class="grafica">
      <h3>{{nodo.replace('_',' ')}}</h3>
      <canvas id="chart-{{nodo}}"></canvas>
    </div>
  {% endfor %}
  <a href="/" class="btn-back">⬅️ Volver al Inicio</a>
<script>
async function cargarGraficas() {
  let res = await fetch('/graficas-json');
  let data = await res.json();
  Object.entries(data).forEach(([nodo, valores]) => {
    const ctx = document.getElementById('chart-' + nodo).getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: Array(valores.length).fill('').map((_, i) => i + 1),
        datasets: [{
          label: 'Actividad',
          data: valores,
          borderColor: '#00ffe7',
          backgroundColor: 'rgba(0, 255, 231, 0.2)',
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: '#00ffe733' } },
          x: { grid: { color: '#00ffe733' } }
        },
        plugins: { legend: { labels: { color: '#00ffe7' } } },
        animation: false
      }
    });
  });
}
cargarGraficas();
setInterval(cargarGraficas, 10000);
</script>
</body>
</html>
'''

HTML_TRAFICO = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Tráfico de Red</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body { background: #121212; color: #00ffe7; font-family: 'Segoe UI'; margin: 0; padding: 2rem; }
  h1 { font-size: 2.8rem; margin-bottom: 1rem; text-align: center; text-shadow: 0 0 10px #00ffe7; }
  table { border-collapse: collapse; width: 90%; max-width: 700px; margin: 1rem auto; background: #222; border-radius: 15px; box-shadow: 0 0 20px #00ffe7aa; overflow: hidden; }
  th, td { padding: 1rem; border-bottom: 1px solid #00ffe7bb; font-weight: 600; }
  th { background: #0052d4; }
  tr:hover { background: #00ffe733; }
  a.btn-back { display: block; margin: 2rem auto 0; width: max-content; color: #00ffe7; text-decoration: none; font-weight: 600; font-size: 1.2rem; text-align: center; }
  a.btn-back:hover { text-decoration: underline; }
</style>
</head>
<body>
  <h1>📊 Tráfico de Red</h1>
  <div id="tabla"></div>
  <a href="/" class="btn-back">⬅️ Volver al Inicio</a>
<script>
async function cargar() {
  let res = await fetch('/trafico-json');
  let data = await res.json();
  let html = "<table><tr><th>Nodo</th><th>Enviado (KB)</th><th>Recibido (KB)</th></tr>";
  data.forEach(r => { html += `<tr><td>${r.Nodo.replace('_',' ')}</td><td>${r.Enviado}</td><td>${r.Recibido}</td></tr>`; });
  html += "</table>";
  document.getElementById('tabla').innerHTML = html;
}
cargar();
setInterval(cargar, 10000);
</script>
</body>
</html>
'''

HTML_TOPOLOGIA = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Topología</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body { background: #121212; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #00ffe7; font-family: 'Segoe UI'; margin: 0; padding: 2rem; }
  h1 { font-size: 2.8rem; margin-bottom: 2rem; text-shadow: 0 0 15px #00ffe7; }
  img { max-width: 90vw; max-height: 70vh; border-radius: 20px; box-shadow: 0 0 30px #00ffe7bb; }
  a.btn-back { margin-top: 2rem; color: #00ffe7; text-decoration: none; font-weight: 600; font-size: 1.2rem; }
  a.btn-back:hover { text-decoration: underline; }
</style>
</head>
<body>
  <h1>🗺️ Topología de Red</h1>
  <img src="/topologia-img" alt="Imagen de Topología" />
  <a href="/" class="btn-back">⬅️ Volver al Inicio</a>
</body>
</html>
'''

HTML_COMANDOS = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Ejecutar Comandos</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body { background: #121212; color: #00ffe7; font-family: 'Segoe UI'; margin: 0; padding: 2rem; display: flex; flex-direction: column; align-items: center; }
  h1 { margin-bottom: 2rem; text-shadow: 0 0 15{Ceiling Fan}px #00ffe7; }
  form { background: #222; padding: 1.5rem; border-radius: 15px; box-shadow: 0 0 20px #00ffe7aa; max-width: 600px; width: 100%; }
  label { font-weight: 600; margin-bottom: .5rem; display: block; }
  select, input[type=text] { width: 100%; padding: .6rem; margin-bottom: 1.2rem; border-radius: 8px; border: none; background: #000; color: #0ff; font-family: monospace; font-size: 1rem; }
  button { background: linear-gradient(135deg, #00ffc8, #0052d4); border: none; padding: .9rem 2rem; font-weight: 700; font-size: 1.2rem; border-radius: 12px; color: #fff; cursor: pointer; box-shadow: 0 0 15px #00ffc8; transition: transform .3s, box-shadow .3s; }
  button:hover { transform: scale(1.05); box-shadow: 0 0 30px #00ffe7; }
  pre { background: #000; color: #0f0; margin-top: 2rem; padding: 1rem; border-radius: 15px; max-height: 300px; overflow-y: auto; font-family: monospace; font-size: 1rem; box-shadow: 0 0 10px #00ff99; }
  a.btn-back { margin-top: 2rem; color: #00ffe7; font-weight: 600; font-size: 1.2rem; text-decoration: none; }
  a.btn-back:hover { text-decoration: underline; }
</style>
</head>
<body>
  <h1>💻 Ejecutar Comandos</h1>
  <form method="POST" autocomplete="off">
    <label for="nodo">Selecciona el dispositivo:</label>
    <select id="nodo" name="nodo" required>
      {% for nodo in nodos %}
        <option value="{{nodo}}" {% if nodo==nodo_seleccionado %}selected{% endif %}>{{nodo.replace('_',' ')}}</option>
      {% endfor %}
    </select>
    <label for="comando">Comando a ejecutar:</label>
    <input type="text" id="comando" name="comando" placeholder="Ejemplo: ipconfig /all o docker ps" value="{{comando or ''}}" required />
    <button type="submit">Ejecutar</button>
  </form>
  {% if salida %}<pre>{{salida}}</pre>{% endif %}
  <a href="/" class="btn-back">⬅️ Volver al Inicio</a>
</body>
</html>
'''

HTML_NMAP = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Escaneo Nmap</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body { background: #121212; color: #0ff; font-family: monospace; padding: 2rem; }
  h1 { text-align: center; text-shadow: 0 0 10px #00ffe7; }
  form { background: #222; padding: 1.5rem; border-radius: 15px; max-width: 600px; margin: auto; }
  label, select, button { display: block; width: 100%; margin: 1rem 0; padding: .6rem; border-radius: 10px; font-size: 1rem; }
  pre { background: #000; padding: 1rem; border-radius: 10px; white-space: pre-wrap; margin-top: 2rem; color: #0f0; }
  a { color: #00ffe7; text-decoration: none; display: block; text-align: center; margin-top: 2rem; }
</style>
</head>
<body>
  <h1>🛡️ Escaneo de Vulnerabilidades con Nmap</h1>
  <form method="POST">
    <label>Selecciona el nodo:</label>
    <select name="nodo" required>
      {% for nodo in nodos %}
        <option value="{{nodo}}">{{nodo.replace('_',' ')}}</option>
      {% endfor %}
    </select>
    <label>Modo de escaneo:</label>
    <select name="modo" required>
      <option value="rapido">Rápido (-sS)</option>
      <option value="agresivo">Agresivo (-A)</option>
    </select>
    <button type="submit">Iniciar Escaneo</button>
  </form>
  {% if salida %}<pre>{{salida}}</pre>{% endif %}
  <a href="/">⬅️ Volver al Inicio</a>
</body>
</html>
'''

HTML_HISTORIAL = '''
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Historial de Comandos</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  body { background: #121212; color: #00ffe7; font-family: 'Segoe UI'; margin: 0; padding: 2rem; }
  h1 { font-size: 2.8rem; margin-bottom: 1rem; text-align: center; text-shadow: 0 0 10px #00ffe7; }
  table { border-collapse: collapse; width: 90%; max-width: 900px; margin: 1rem auto; background: #222; border-radius: 15px; box-shadow: 0 0 20px #00ffe7aa; overflow: hidden; }
  th, td { padding: 1rem; border-bottom: 1px solid #00ffe7bb; font-weight: 600; }
  th { background: #0052d4; }
  tr:hover { background: #00ffe733; }
  pre { white-space: pre-wrap; margin: 0; color: #0f0; font-family: monospace; }
  a.btn-back { display: block; margin: 2rem auto 0; width: max-content; color: #00ffe7; text-decoration: none; font-weight: 600; font-size: 1.2rem; text-align: center; }
  a.btn-back:hover { text-decoration: underline; }
</style>
</head>
<body>
  <h1>📜 Historial de Comandos</h1>
  <div id="tabla"></div>
  <a href="/" class="btn-back">⬅️ Volver al Inicio</a>
<script>
async function cargar() {
  let res = await fetch('/historial-json');
  let data = await res.json();
  let html = "<table><tr><th>Hora</th><th>Nodo</th><th>Comando</th><th>Salida</th></tr>";
  data.forEach(r => {
    html += `<tr><td>${r.hora}</td><td>${r.nodo.replace('_',' ')}</td><td>${r.comando}</td><td><pre>${r.salida}</pre></td></tr>`;
  });
  html += "</table>";
  document.getElementById('tabla').innerHTML = html;
}
cargar();
setInterval(cargar, 10000);
</script>
</body>
</html>
'''

# --- Rutas ---
@app.route('/')
def home():
    return render_template_string(HTML_HOME)

@app.route('/nodos')
def nodos():
    return render_template_string(HTML_NODOS)

@app.route('/estado-json')
def estado_json():
    return jsonify({nombre: ping_node(ip) for nombre, ip in NODOS.items()})

@app.route('/graficas')
def graficas():
    return render_template_string(HTML_GRAFICAS, nodos=NODOS.keys())

@app.route('/graficas-json')
def graficas_json():
    for nodo in historico_nodos:
        valores = historico_nodos[nodo]
        nuevo = max(0, min(100, valores[-1] + random.randint(-10, 10)))
        valores.append(nuevo)
        if len(valores) > 20:
            valores.pop(0)
    return jsonify(historico_nodos)

@app.route('/trafico')
def trafico_page():
    return render_template_string(HTML_TRAFICO)

@app.route('/trafico-json')
def trafico_json():
    for r in trafico_red:
        r['Enviado'] = random.randint(100, 1000)
        r['Recibido'] = random.randint(200, 1500)
    return jsonify(trafico_red)

@app.route('/topologia')
def topologia_page():
    return render_template_string(HTML_TOPOLOGIA)

@app.route('/topologia-img')
def topologia_img():
    ruta = os.path.join(os.path.dirname(__file__), 'topologia.png')
    try:
        if os.path.exists(ruta):
            return send_file(ruta, mimetype='image/png')
    except Exception as e:
        print(f"Error accessing topology image: {e}")
    # Fallback: Return a placeholder image
    return jsonify({"error": "Topología no disponible"}), 404

@app.route('/comandos', methods=['GET', 'POST'])
def comandos():
    salida = None
    nodo_sel = None
    comando = None
    allowed_commands = ['ipconfig /all', 'docker ps', 'ping -c 4']
    if request.method == 'POST':
        nodo_sel = request.form.get('nodo')
        comando = request.form.get('comando')
        if nodo_sel in NODOS and comando in allowed_commands:
            # Simulate command output for testing
            fake_outputs = {
                'ipconfig /all': f"Windows IP Configuration\n   Host Name: {nodo_sel}\n   IP Address: {NODOS[nodo_sel]}",
                'docker ps': "CONTAINER ID   IMAGE          COMMAND                  CREATED        STATUS        PORTS\n1234567890ab   nginx:latest   \"nginx -g 'daemon off'\"   5 minutes ago   Up 5 minutes   80/tcp",
                'ping -c 4': f"PING {NODOS[nodo_sel]} ({NODOS[nodo_sel]}): 56 data bytes\n64 bytes from {NODOS[nodo_sel]}: icmp_seq=0 ttl=64 time={random.uniform(0.1, 1):.3f} ms"
            }
            salida = escape(fake_outputs.get(comando, "Comando ejecutado sin salida"))
            historial_comandos.append({
                'hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'nodo': nodo_sel,
                'comando': comando,
                'salida': salida
            })
        else:
            salida = escape("Comando no permitido o nodo inválido")
    return render_template_string(HTML_COMANDOS, nodos=NODOS.keys(), salida=salida, nodo_seleccionado=nodo_sel, comando=comando)

@app.route('/historial')
def historial_page():
    return render_template_string(HTML_HISTORIAL)

@app.route('/historial-json')
def historial_json():
    return jsonify(historial_comandos)

@app.route('/nmap', methods=['GET', 'POST'])
def nmap_scan():
    salida = None
    if request.method == 'POST':
        nodo = request.form.get('nodo')
        modo = request.form.get('modo')
        ip = NODOS.get(nodo)
        if ip and modo in ['rapido', 'agresivo']:
            # Simulate nmap output for testing
            nmap_flag = '-A' if modo == 'agresivo' else '-sS'
            fake_output = f"Nmap scan report for {nodo} ({ip})\nHost is up (0.01s latency).\nPORT   STATE SERVICE\n80/tcp open  http\n"
            if modo == 'agresivo':
                fake_output += "OS: Linux 5.x\nService Info: Apache/2.4.41\n"
            salida = escape(fake_output)
        else:
            salida = escape("Nodo o modo inválido")
    return render_template_string(HTML_NMAP, nodos=NODOS.keys(), salida=salida)

if __name__ == '__main__':
    app.run(debug=True, port=5000)