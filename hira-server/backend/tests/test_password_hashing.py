"""Núcleo — hashing de contraseñas. Sin I/O, sin mocks, bcrypt real.

Cubre RF-012 (`spec.md`): passwords se almacenan con bcrypt factor 12, nunca en
texto plano.
"""
from core.security.passwords import hash_password, verify_password

PLAIN_PASSWORD = "Sup3r-S3cret!"


def test_hash_password_nunca_es_igual_al_texto_plano():
    password_hash = hash_password(PLAIN_PASSWORD)

    assert password_hash != PLAIN_PASSWORD


def test_hash_password_usa_bcrypt_factor_12():
    password_hash = hash_password(PLAIN_PASSWORD)

    # Formato bcrypt: $2b$<rounds>$<22-char-salt><31-char-hash>
    assert password_hash.startswith("$2b$12$")


def test_verify_password_acepta_el_password_correcto():
    password_hash = hash_password(PLAIN_PASSWORD)

    assert verify_password(PLAIN_PASSWORD, password_hash) is True


def test_verify_password_rechaza_el_password_incorrecto():
    password_hash = hash_password(PLAIN_PASSWORD)

    assert verify_password("password-incorrecto", password_hash) is False


def test_hash_password_es_distinto_en_cada_llamada_mismo_password():
    # bcrypt genera un salt aleatorio por invocación — dos hashes del mismo
    # password nunca deben coincidir en texto.
    assert hash_password(PLAIN_PASSWORD) != hash_password(PLAIN_PASSWORD)
