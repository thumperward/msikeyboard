FROM mcr.microsoft.com/vscode/devcontainers/base:debian

# Install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends \
  python3-pip \
  npm

# Install Python packages needed outside of Poetry.
RUN pip3 install \
  poetry \
  pre-commit \
  detect-secrets

# Install Node packages.
RUN npm install -g \
  markdownlint-cli
