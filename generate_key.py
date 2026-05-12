import secrets
print("Your Flask Secret Key is:")
print(secrets.token_hex(32))