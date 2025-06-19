# Define phony targets to prevent issues if a file named 'clean' or 'install-deps' exists
.PHONY: find-native all clean quick install-deps

find-native:
	@find node_modules -type f -name "*.node" 2>/dev/null | grep -v "obj\.target"

# Main target to build everything for release
all: install-deps
	@echo "Running electron-rebuild..."
	@npm run electron-rebuild
	@echo "Building stubs..."
	@./scripts/build-stubs.py
	@echo "Packaging VS Code extension..."
	@npx @vscode/vsce package
	@echo "All build steps complete."

# Quick package target for faster iteration
quick: install-deps
	@echo "Packaging VS Code extension quickly..."
	@npx @vscode/vsce package
	@echo "Quick package complete."

# Target to clean up node_modules and package-lock.json
clean:
	@echo "Cleaning node_modules and package-lock.json..."
	rm -rf node_modules
	rm -f package-lock.json
	@echo "Clean complete."

# Optional: A target to clean and then reinstall dependencies
# This is often useful after a 'clean' to get a fresh start
install-deps: clean
	@echo "Installing npm dependencies..."
	npm install
	@echo "Dependency installation complete."