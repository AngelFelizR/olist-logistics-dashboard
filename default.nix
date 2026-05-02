let
  # Import a specific version of nixpkgs (frozen for reproducibility)
  pkgs = import (fetchTarball "https://github.com/rstats-on-nix/nixpkgs/archive/2026-04-22.tar.gz") {};

  # Python packages to be included in the environment
  pyconf = builtins.attrValues {
    inherit (pkgs.python313Packages)
      pip
      ipykernel
      jupyter
      # Core Data Stack
      pandas        # Pandas with Arrow backend support
      pyarrow       # High-performance backend for Pandas
      numpy
      # Visualization
      plotnine      # Grammar of Graphics (ggplot2 style for Python)
      # Scientific computing
      scipy
      # NLP
      spacy
      unidecode     # Para normalizar caracteres brasileños
      tqdm          # Para monitorear el progreso en reviews largas
      # Machine Learning
      scikit-learn
      # Package development and testing
      pytest
      pytest-cov
      black         # Code formatter
      quartodoc;    # Documentation generator
  };

  # System-level packages (non-Python)
  system_packages = builtins.attrValues {
    inherit (pkgs)
      glibcLocales
      nix
      python313
      uv            # Fast Python package installer and resolver
      quarto
      fontconfig
      dejavu_fonts    # Standard fonts
      freefont_ttf    # Additional fonts for better rendering
      liberation_ttf; # Metric-compatible fonts (Arial/Times)
  };

  # Define the development shell
  shell = pkgs.mkShell {
    # Locale configuration for consistent behavior
    LOCALE_ARCHIVE = if pkgs.system == "x86_64-linux" 
      then "${pkgs.glibcLocales}/lib/locale/locale-archive" 
      else "";
    
    LANG = "en_US.UTF-8";
    LC_ALL = "en_US.UTF-8";

    # Fontconfig setup so Matplotlib can find fonts installed by Nix
    FONTCONFIG_FILE = "${pkgs.fontconfig.out}/etc/fonts/fonts.conf";

    shellHook = ''
      # 1. Configure font paths for Matplotlib and other tools
      export XDG_DATA_DIRS="${pkgs.dejavu_fonts}/share:${pkgs.freefont_ttf}/share:${pkgs.liberation_ttf}/share:$XDG_DATA_DIRS"
      fc-cache -f 2>/dev/null || true

      # 2. Add source directory to PYTHONPATH for immediate development
      #    This allows `import OlistProject` without installation
      export PYTHONPATH=$PWD/src:$PYTHONPATH

      # 3. Install package in editable mode using uv (recommended for real development)
      #    --system is required because we are inside a Nix environment (no venv)
      echo "→ Installing OlistProject in editable mode (--system)..."
      uv pip install -e . --system --reinstall --quiet || true
      echo "✅ OlistProject package installed in editable mode"

      # Languague model
      uv pip install https://github.com/explosion/spacy-models/releases/download/pt_core_news_sm-3.8.0/pt_core_news_sm-3.8.0-py3-none-any.whl --system --quiet || true
    '';

    # All packages that will be available inside the shell
    buildInputs = [ pyconf system_packages ];
  };
in
  {
    inherit pkgs shell;
  }
