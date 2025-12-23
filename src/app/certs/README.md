# RSA Key Generation for JWT

To ensure secure authentication, you need to generate a pair of RSA keys (private and public). These keys are used for signing and verifying tokens.

## 🔑 Generate via OpenSSL

Run the following commands in this directory (`src/app/certs/`):

### 1. Generate a Private Key
This command creates a 2048-bit RSA private key.
```bash
openssl genrsa -out jwt-private.pem 2048
```

### 2. Extract the Public Key
This command extracts the public key from the pair, which will be used for token verification.
```bash
openssl rsa -in jwt-private.pem -outform PEM -pubout -out jwt-public.pem
```