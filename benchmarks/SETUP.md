### System Configuration & OS Limits

```bash
# Increase the maximum number of open files
ulimit -n 65535

# Adjust network buffer sizes
sudo sysctl -w net.core.rmem_max=2500000
sudo sysctl -w net.core.wmem_max=2500000

# Increase the size of the incoming connection queue
sudo sysctl -w net.core.somaxconn=2048

# Allow memory overcommitment
sudo sysctl -w vm.overcommit_memory=1
```

* **Note on Docker:**
  * If services are running inside containers, `ulimit` settings are not inherited from the host. They must be set separately for containers (e.g., by adding `--ulimit nofile=65535:65535` to the run command or via the `ulimits` key in `compose.yaml`).
  * **`sysctl`** settings (network buffers, `somaxconn`, `overcommit_memory`) are applied at the **host OS** level. Since containers share the host's kernel, these optimizations will affect them automatically. It is not necessary (and usually forbidden) to execute them inside a container.
* **Cross-platform compatibility:** The provided `sysctl` and `ulimit` parameters are standardized for Linux distributions (Debian, Ubuntu, etc.). For macOS or Windows (WSL), alternative kernel settings apply.

### Proxy Configuration (Angie) for Load Testing
Modify the configuration to prevent the proxy from throttling the benchmarking tool:

```nginx
location / {
    # Comment out rate limits for load testing
    # limit_req zone=api_limit burst=30 nodelay;
    # limit_conn addr_limit 20;
}

upstream app_backend {
    # Set max_fails=0 to prevent Angie from marking the backend as "down" under stress
    server unix:/run/app/granian.sock max_fails=0;
}
```

### SSL certificate generation (mkcert)
```bash
# Install local CA
mkcert -install

# Generate certificates for the app.localhost domain
mkdir -p deploy/certs
mkcert -cert-file deploy/certs/local-cert.pem -key-file deploy/certs/local-key.pem app.localhost localhost 127.0.0.1 ::1
```