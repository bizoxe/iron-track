# Issue RSA private key + public key pair

Generate an RSA private key, of size 2048

openssl genrsa -out jwt-private.pem 2048

Extract the public key from key pair, which can be used in certificate

openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
