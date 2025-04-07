FROM ghcr.io/jac18281828/python3:latest

WORKDIR /workspaces/megaswap

COPY . .

USER py3
