#!/bin/bash

# 1. Build the Docker image locally (important because Nix builds inside Docker)
echo "Building Nix environment inside Docker..."
docker compose build

# 2. Start the container in detached mode
docker compose up -d

# 3. Wait a moment for SSH to be ready and inject the public SSH key
# We use a pipe to avoid creating temporary files inside the container
cat ~/.ssh/id_rsa.pub | docker compose exec -T olist-dashboard bash -c "cat >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys"

echo "-------------------------------------------------------"
echo "✅ OlistProject environment successfully deployed!"
echo "🚀 Connect with: ssh root@localhost -p 2225"
echo "📂 Remember to open the folder /root/olist-logistics-dashboard in Positron"
echo "-------------------------------------------------------"
