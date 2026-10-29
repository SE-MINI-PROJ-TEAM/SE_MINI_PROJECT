"""Generate a self-signed certificate for local HTTPS testing (PRJ-SR-001).

    python scripts/gen_dev_cert.py        -> backend/certs/dev-cert.pem + dev-key.pem
    python run.py --https                 -> serves with a TLS 1.3 minimum
    (set ENFORCE_HTTPS=true in .env to also redirect HTTP, send HSTS and mark cookies Secure)

Development only - production terminates TLS 1.3 at the reverse proxy with a CA-issued certificate.
"""
import datetime
import ipaddress
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

DEFAULT_CERT_DIR = os.path.join(os.path.dirname(__file__), "..", "certs")


def generate(cert_dir=DEFAULT_CERT_DIR):
    os.makedirs(cert_dir, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    with open(os.path.join(cert_dir, "dev-key.pem"), "wb") as f:
        f.write(
            key.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()
            )
        )
    with open(os.path.join(cert_dir, "dev-cert.pem"), "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    return cert_dir


if __name__ == "__main__":
    path = generate()
    print(f"Wrote {os.path.normpath(path)}/dev-cert.pem and dev-key.pem (valid 365 days, localhost / 127.0.0.1)")
