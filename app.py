import os
import sys
import webbrowser
from pathlib import Path
from threading import Timer


def _bootstrap_venv():
    if os.environ.get('VIRTUAL_ENV'):
        return
    venv_python = Path(__file__).resolve().parent / 'venv' / 'bin' / 'python3'
    if venv_python.exists():
        os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])


_bootstrap_venv()

from app.factory import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    url = f'http://localhost:{port}/admin/login'

    def open_browser():
        webbrowser.open(url)

    Timer(1, open_browser).start()
    app.run(debug=True, port=port, host='0.0.0.0')
