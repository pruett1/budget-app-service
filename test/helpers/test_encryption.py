from src.helpers.encryption import pwd_hash, encrypt, decrypt

def test_pwd_hash():
    test_password = "test_password"

    hashed_password = pwd_hash(test_password)

    assert test_password != hashed_password # hashes properly
    assert hashed_password == pwd_hash(test_password) # is consistent

def test_encrypt_decrypt():
    data = "some test data"

    encrypted_data = encrypt(data)
    decrypted_data = decrypt(encrypted_data)

    assert data != encrypted_data # data is encrypted
    assert encrypted_data != encrypt(data) # random encryption
    assert data == decrypted_data # data is decrypted properly