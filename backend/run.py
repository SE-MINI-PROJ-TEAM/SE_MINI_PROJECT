"""Development entry point.

    python run.py            # http://localhost:5000
    python run.py --https    # https://localhost:5000 with TLS 1.3 minimum (needs certs from scripts/gen_dev_cert.py)
"""
import argparse
import os
import ssl

from app import create_app

app = create_app()

CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")


def build_ssl_context(cert_dir=CERT_DIR):
    """Server-side TLS context that refuses anything older than TLS 1.3 (PRJ-SR-001)."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(os.path.join(cert_dir, "dev-cert.pem"), os.path.join(cert_dir, "dev-key.pem"))
    return context


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--https", action="store_true", help="serve over TLS 1.3 using certs/dev-cert.pem")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    app.run(
        host="0.0.0.0",
        port=args.port,
        debug=os.getenv("FLASK_ENV") == "development",
        threaded=True,
        ssl_context=build_ssl_context() if args.https else None,
    )
