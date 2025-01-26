FROM node:20-slim AS base

# Enable pnpm
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package.json ./package.json
COPY frontend/pnpm-lock.yaml ./pnpm-lock.yaml

# Install dependencies
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install

# # Copy the rest of the frontend code
COPY frontend/ ./

CMD ["pnpm", "dev"] 