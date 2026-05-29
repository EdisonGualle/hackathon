"""
Lanzador público de FRAUDIA: arranca Streamlit y abre un túnel ngrok.
Uso:
    python run_publico.py

Imprime el ENLACE PÚBLICO que puedes compartir con el jurado.
Detén todo con Ctrl + C.

Requisitos (una sola vez):
    pip install pyngrok
El token de ngrok se toma de la variable de entorno NGROK_TOKEN.
"""

import os
import sys
import time
import socket
import subprocess

PORT = 8501

# Token de ngrok. No lo dejes escrito en el repositorio.
NGROK_TOKEN = os.getenv("NGROK_TOKEN", "")


def _puerto_arriba(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    # 1) Arrancar Streamlit en segundo plano
    print("Iniciando FRAUDIA (Streamlit)…")
    streamlit_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", str(PORT),
         "--server.headless", "true",
         "--server.enableCORS", "false",
         "--server.enableXsrfProtection", "false"],
        cwd=here,
    )

    # 2) Esperar a que el servidor responda
    print("Esperando a que el servidor esté listo…")
    for _ in range(90):
        if _puerto_arriba(PORT):
            break
        time.sleep(1)
    else:
        print("ERROR: Streamlit no levantó a tiempo.")
        streamlit_proc.terminate()
        return

    # 3) Abrir el túnel ngrok
    try:
        from pyngrok import ngrok, conf
    except ImportError:
        print("\nFalta pyngrok. Instálalo con:  pip install pyngrok\n")
        streamlit_proc.terminate()
        return

    if not NGROK_TOKEN:
        print("\nFalta NGROK_TOKEN. Defínelo en tu entorno o archivo .env antes de abrir el túnel.\n")
        streamlit_proc.terminate()
        return

    conf.get_default().auth_token = NGROK_TOKEN
    for t in ngrok.get_tunnels():
        ngrok.disconnect(t.public_url)
    tunnel = ngrok.connect(PORT, "http")

    print("\n" + "=" * 60)
    print("  FRAUDIA ESTÁ EN LÍNEA")
    print("  Enlace público (compártelo):")
    print("   ", tunnel.public_url)
    print("=" * 60)
    print("  (Local: http://localhost:%d)" % PORT)
    print("  Detén todo con Ctrl + C.\n")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nCerrando túnel y servidor…")
    finally:
        try:
            ngrok.disconnect(tunnel.public_url)
            ngrok.kill()
        except Exception:
            pass
        streamlit_proc.terminate()


if __name__ == "__main__":
    main()
