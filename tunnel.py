from pyngrok import ngrok, conf
import time, sys

conf.get_default().auth_token = '2xDzWy3i6iogkWGpKT9JPa4QpCg_5YGZ16Se4ybELrKFscvjv'

# Cerrar tuneles previos si existen
for t in ngrok.get_tunnels():
    ngrok.disconnect(t.public_url)

tunnel = ngrok.connect(8501, 'http')
print('PUBLIC_URL:', tunnel.public_url, flush=True)

# Mantener vivo
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    ngrok.disconnect(tunnel.public_url)
    ngrok.kill()
