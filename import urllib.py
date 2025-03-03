import urllib.parse

password = "contraseña@123"
encoded_password = urllib.parse.quote(password)
print(encoded_password)  # Salida: contrase%C3%B1a%40123