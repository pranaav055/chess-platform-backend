from app.core.password_security import hash_password, verify_password


plain_password = "chess123"

hashed = hash_password(plain_password)

print("Plain password:", plain_password)
print("Hashed password:", hashed)

print("Correct password works:", verify_password("chess123", hashed))
print("Wrong password works:", verify_password("wrongpassword", hashed))