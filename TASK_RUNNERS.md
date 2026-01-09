# Task Runners Guide

This project supports three ways to run tasks:

1. **`just`** (Recommended) - Modern, simple, cross-platform
2. **`make`** (Fallback) - Traditional, universally available
3. **Scripts** (Manual) - Direct shell/PowerShell scripts

## Why Use Task Runners?

- ✅ **Single command** to run complex workflows
- ✅ **Reproducible** - Same commands work for everyone
- ✅ **Self-documenting** - Easy to see what's available
- ✅ **Error handling** - Built-in checks and validations
- ✅ **Cross-platform** - Works on Windows, macOS, Linux

## Quick Start

### Option 1: Using `just` (Recommended)

**Install just:**
```bash
# macOS
brew install just

# Linux
cargo install just
# or
wget -qO - 'https://proget.makedeb.org/debian-feeds/prebuilt-mpr.pub' | gpg --dearmor | sudo tee /usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg 1> /dev/null
echo "deb [arch=all,$(dpkg --print-architecture) signed-by=/usr/share/keyrings/prebuilt-mpr-archive-keyring.gpg] https://proget.makedeb.org prebuilt-mpr $(lsb_release -cs)" | sudo tee /etc/apt/sources.list.d/prebuilt-mpr.list
sudo apt update && sudo apt install just

# Windows (using cargo or scoop)
cargo install just
# or
scoop install just
```

**Use just:**
```bash
just --list           # Show all available commands
just setup            # Complete first-time setup
just run-basic        # Run without ML
just train            # Train model
just run-ml           # Run with ML
just health           # System health check
```

### Option 2: Using `make` (Fallback)

Make is pre-installed on macOS/Linux. For Windows, use WSL or install via chocolatey.

```bash
make help             # Show all available commands
make setup            # Complete first-time setup
make run-basic        # Run without ML
make train            # Train model
make run-ml           # Run with ML
make health           # System health check
```

### Option 3: Using Scripts Directly

See [SCRIPTS.md](SCRIPTS.md) for manual script usage.

## Complete Workflow Examples

### Using `just`:

```bash
# First time setup
just setup

# Accumulate training data (let run 5-10 minutes)
just run-basic

# Check data (in another terminal)
just check

# Train model (after stopping processor with Ctrl+C)
just train

# Run with ML predictions
just run-ml

# Check ML performance
just check-ml

# View system health
just health
```

### Using `make`:

```bash
# First time setup
make setup

# Accumulate training data (let run 5-10 minutes)
make run-basic

# Check data (in another terminal)
make check

# Train model (after stopping processor with Ctrl+C)
make train

# Run with ML predictions
make run-ml

# Check ML performance
make check-ml

# View system health
make health
```

## Common Tasks Reference

| Task | `just` Command | `make` Command | Description |
|------|---------------|----------------|-------------|
| **Setup** |
| First-time setup | `just setup` | `make setup` | Install deps, start services |
| Start services | `just start` | `make start` | Start Docker containers |
| Stop services | `just stop` | `make stop` | Stop Docker containers |
| Check status | `just status` | `make status` | Show container status |
| **Processing** |
| Run basic processor | `just run-basic` | `make run-basic` | Without ML |
| Train model | `just train` | `make train` | Train Random Forest |
| Run with ML | `just run-ml` | `make run-ml` | With ML predictions |
| **Monitoring** |
| Check data | `just check` | `make check` | MongoDB statistics |
| Check ML | `just check-ml` | `make check-ml` | ML performance |
| View logs | `just logs` | `make logs` | All service logs |
| Health check | `just health` | `make health` | Complete system check |
| **Maintenance** |
| Clean all | `just clean` | `make clean` | Delete all data |
| Clean model | `just clean-model` | `make clean-model` | Remove model |
| Reset producer | `just reset-producer` | `make reset-producer` | Restart from beginning |
| **Development** |
| Spark shell | `just shell-spark` | `make shell-spark` | Enter Spark container |
| Mongo shell | `just shell-mongo` | `make shell-mongo` | Enter MongoDB |
| Check model | `just check-model` | `make check-model` | Verify model exists |
| **UI** |
| Open Mongo Express | `just ui-mongo` | `make ui-mongo` | Browser: MongoDB UI |
| Open Dozzle | `just ui-logs` | `make ui-logs` | Browser: Log viewer |

## Advanced Features

### `just` Exclusive Features

**Interactive workflow:**
```bash
just workflow-interactive
```
Guides you through the complete ML workflow with prompts.

**Run custom Python script:**
```bash
just run-script train_model.py
```

**View specific service logs:**
```bash
just log spark      # Follow Spark logs in real-time
```

### `make` Exclusive Features

**View specific service logs:**
```bash
make log-spark      # Follow Spark logs
make log-kafka      # Follow Kafka logs
```

## Comparison: `just` vs `make`

| Feature | `just` | `make` |
|---------|--------|--------|
| Installation | Needs manual install | Pre-installed on Unix |
| Syntax | Simple, readable | More complex |
| Cross-platform | Excellent | Good (with GNU make) |
| Shell support | Modern bash features | POSIX compatible |
| Learning curve | Easy | Moderate |
| Features | Rich (recipes, variables) | Powerful (dependencies) |
| **Recommendation** | ⭐ Primary choice | ✅ Fallback option |

## Troubleshooting

### `just` not found
```bash
# Install just
brew install just           # macOS
cargo install just          # All platforms with Rust
```

### `make` not found (Windows)
```bash
# Use WSL or install via chocolatey
choco install make
```

### Permission denied
```bash
# Make scripts executable
chmod +x *.sh
```

### Docker not running
```bash
# Both tools will show clear error:
# "Docker is not running!"
# Start Docker Desktop and try again
```

## Best Practices

1. **Use `just` for development** - More readable, better error messages
2. **Use `make` for CI/CD** - More universally available
3. **Use scripts directly** - When learning or debugging
4. **Check health regularly** - Run `just health` or `make health`
5. **Always stop processor** (Ctrl+C) before training model
6. **Monitor data accumulation** - Use `just check` to verify progress

## Contributing

When adding new tasks:
1. Add to `justfile` (with description and helpful messages)
2. Add equivalent to `Makefile` (with ## comment)
3. Update this documentation
4. Test on multiple platforms
