# Example Kubernetes secret — apply manually, never commit real values.
#
# kubectl create secret generic voxera-api-secrets \
#   --from-literal=JWT_SECRET_KEY="$(openssl rand -base64 32)" \
#   --from-literal=API_KEY_SECRET="$(openssl rand -base64 32)" \
#   --from-literal=ENCRYPTION_SECRET_KEY="$(openssl rand -base64 32)" \
#   --from-literal=DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/voxera"
#
# External Secrets (future):
#   AWS Secrets Manager  → secrets.provider: aws
#   Azure Key Vault      → secrets.provider: azure
#   GCP Secret Manager   → secrets.provider: gcp
#   HashiCorp Vault      → secrets.provider: vault
