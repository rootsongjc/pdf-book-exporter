#!/bin/bash

# Install dependencies for PDF export script
# This script installs the necessary tools for converting Hugo books to PDF

echo "Installing PDF export dependencies..."

# --- OS Detection and Installation ---
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS, installing with Homebrew..."
    
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install it first."
        exit 1
    fi
    
    echo "Installing system dependencies: pandoc, librsvg, imagemagick, basictex..."
    brew install pandoc librsvg imagemagick
    brew install --cask basictex
    
    echo "Installing LaTeX packages via tlmgr..."
    sudo tlmgr update --self
    sudo tlmgr install ctex fancyhdr titlesec fontspec geometry chngcntr booktabs caption float framed hyperref listings parskip fvextra

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux..."
    
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Using apt-get..."
        sudo apt-get update
        sudo apt-get install -y \
            pandoc \
            librsvg2-bin \
            imagemagick \
            texlive-latex-base \
            texlive-latex-recommended \
            texlive-latex-extra \
            texlive-xetex \
            texlive-lang-chinese \
            texlive-font-utils \
            texlive-luatex
            
    elif command -v dnf &> /dev/null || command -v yum &> /dev/null; then
        # Fedora/CentOS/RHEL
        echo "Using dnf/yum..."
        if command -v dnf &> /dev/null; then
            PKG_MANAGER=dnf
        else
            PKG_MANAGER=yum
        fi
        sudo $PKG_MANAGER install -y \
            pandoc \
            librsvg2-tools \
            ImageMagick \
            texlive-latex-base \
            texlive-latex \
            texlive-collection-latexrecommended \
            texlive-collection-latexextra \
            texlive-collection-langchinese \
            texlive-xetex \
            texlive-font-utils \
            texlive-luatex

    elif command -v pacman &> /dev/null; then
        # Arch Linux
        echo "Using pacman..."
        sudo pacman -S --noconfirm --needed \
            pandoc \
            librsvg \
            imagemagick \
            texlive-core \
            texlive-latexextra \
            texlive-langchinese \
            texlive-xetex
            
    else
        echo "Unsupported Linux distribution. Please install dependencies manually."
        exit 1
    fi
    
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo ""
echo "✅ Dependencies installation completed!"
echo ""
echo "To verify installation, run:"
echo "  pandoc --version"
echo "  rsvg-convert --version"
echo "  convert --version"
echo "  xelatex --version"
echo ""
echo "You can now use the PDF export script."
