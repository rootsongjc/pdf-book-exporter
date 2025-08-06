# Makefile for PDF book exporter tools
# Contains utilities for the PDF export system

.PHONY: help clean install diagnostics

# Default target
help:
	@echo "PDF Book Exporter - Available targets:"
	@echo "  install        - Install required dependencies"
	@echo "  diagnostics    - Run system diagnostics for emoji support"
	@echo "  clean          - Clean generated files"
	@echo ""
	@echo "Usage: python cli.py [book_directory] -o [output.pdf] [options]"
	@echo "Run 'python cli.py --help' for more information"

# Install dependencies
install:
	@echo "Installing PDF export dependencies..."
	@chmod +x install_pdf_dependencies.sh
	@./install_pdf_dependencies.sh

# Run system diagnostics
diagnostics:
	@echo "Running PDF export diagnostics..."
	@python3 cli.py --diagnostics .

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	@rm -f *.pdf
	@rm -f emoji-font-config.tex
	@rm -rf test-output
	@echo "Clean complete."
