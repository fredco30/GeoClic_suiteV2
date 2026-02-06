#!/usr/bin/env python3
"""
===========================================================================
GéoClic V12 Pro - Générateur de Certificats SSL pour API
===========================================================================
Génère des certificats auto-signés pour permettre l'accès HTTPS en 4G.
"""

import os
import sys
import datetime
import subprocess
from pathlib import Path

def generate_ssl_certificates():
    """Génère les certificats SSL dans le dossier ssl/"""

    print("=" * 60)
    print("   GéoClic V12 Pro - Génération Certificats SSL (API)")
    print("=" * 60)
    print()

    # Créer le dossier ssl si nécessaire
    ssl_dir = Path(__file__).parent / "ssl"
    ssl_dir.mkdir(exist_ok=True)

    key_file = ssl_dir / "api_server.key"
    cert_file = ssl_dir / "api_server.crt"

    # Configuration du certificat
    ip_publique = "5.48.33.65"

    # Vérifier si OpenSSL est disponible
    try:
        result = subprocess.run(["openssl", "version"], capture_output=True, text=True)
        print(f"   OpenSSL trouvé: {result.stdout.strip()}")
        use_openssl = True
    except FileNotFoundError:
        print("   OpenSSL non trouvé - utilisation de la méthode Python")
        use_openssl = False

    print()

    if use_openssl:
        # Utiliser OpenSSL pour générer les certificats
        print("[1/2] Génération de la clé privée RSA 4096 bits...")

        # Générer la clé privée
        subprocess.run([
            "openssl", "genrsa",
            "-out", str(key_file),
            "4096"
        ], check=True, capture_output=True)
        print("      Clé privée générée")

        print("[2/2] Génération du certificat auto-signé...")

        # Créer le fichier de configuration pour SAN
        san_config = ssl_dir / "san.cnf"
        san_config.write_text(f"""
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
C = FR
ST = France
L = Paris
O = GéoClic
OU = API
CN = {ip_publique}

[v3_req]
subjectAltName = @alt_names
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = {ip_publique}
IP.3 = 0.0.0.0
""")

        # Générer le certificat
        subprocess.run([
            "openssl", "req",
            "-new", "-x509",
            "-key", str(key_file),
            "-out", str(cert_file),
            "-days", "365",
            "-config", str(san_config)
        ], check=True, capture_output=True)

        # Supprimer le fichier de config temporaire
        san_config.unlink()
        print("      Certificat généré")

    else:
        # Méthode Python pure avec cryptography
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend
            import ipaddress
        except ImportError:
            print("ERREUR: Module 'cryptography' non installé")
            print("Installez-le avec: pip install cryptography")
            return False

        print("[1/2] Génération de la clé privée RSA 4096 bits...")

        # Générer la clé privée
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )

        # Sauvegarder la clé privée
        with open(key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        print("      Clé privée générée")

        print("[2/2] Génération du certificat auto-signé...")

        # Construire le certificat
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "France"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Paris"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "GéoClic"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "API"),
            x509.NameAttribute(NameOID.COMMON_NAME, ip_publique),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("*.localhost"),
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                    x509.IPAddress(ipaddress.ip_address(ip_publique)),
                ]),
                critical=False,
            )
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .sign(key, hashes.SHA256(), default_backend())
        )

        # Sauvegarder le certificat
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print("      Certificat généré")

    print()
    print("=" * 60)
    print("   CERTIFICATS GÉNÉRÉS AVEC SUCCÈS")
    print("=" * 60)
    print()
    print(f"   Clé privée:  {key_file}")
    print(f"   Certificat:  {cert_file}")
    print()
    print(f"   Valide pour:")
    print(f"     - localhost")
    print(f"     - 127.0.0.1")
    print(f"     - {ip_publique}")
    print()
    print("   Validité: 365 jours")
    print()
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = generate_ssl_certificates()
    sys.exit(0 if success else 1)
