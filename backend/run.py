"""MiroFish backend entrypoint / Punto di ingresso backend MiroFish."""

import os
import sys

# Fix Windows console encoding issues: force UTF-8 before imports /
# Corregge problemi di codifica console su Windows: forza UTF-8 prima degli import
if sys.platform == 'win32':
    # Ensure Python uses UTF-8 / Assicura che Python usi UTF-8
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    # Reconfigure std streams to UTF-8 / Riconfigura stream standard in UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path / Aggiunge root progetto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """Main function / Funzione principale."""
    # Validate config / Valida configurazione
    errors = Config.validate()
    if errors:
        print("Configuration errors / Errori di configurazione:")
        for err in errors:
            print(f"  - {err}")
        print("\nPlease check .env configuration / Controlla la configurazione nel file .env")
        sys.exit(1)
    
    # Create app / Crea app
    app = create_app()
    
    # Read runtime configuration / Legge configurazione runtime
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = Config.DEBUG
    
    # Start service / Avvia servizio
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()

