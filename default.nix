let
  # Import a specific version of nixpkgs (frozen for reproducibility)
  pkgs = import (fetchTarball "https://github.com/rstats-on-nix/nixpkgs/archive/2026-04-22.tar.gz") {};

  # To Render PDF
  tex = (pkgs.texlive.combine {
    inherit (pkgs.texlive)
      collection-fontsextra
      csquotes
      fancyhdr
      fontawesome5
      fontspec
      makecell
      orcidlink
      pdfcol
      pdflscape
      scheme-medium
      tcolorbox
      threeparttable
      threeparttablex
      tikzfill
      titling;
  });

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
      openpyxl      # Writing excel files
      # Visualization
      plotnine;      # Grammar of Graphics (ggplot2 style for Python)
  };

  # System-level packages (non-Python)
  system_packages = builtins.attrValues {
    inherit (pkgs)
      glibcLocales
      nix
      quarto
      which
      python313
      fontconfig
      dejavu_fonts    # Standard fonts
      freefont_ttf    # Additional fonts for better rendering
      liberation_ttf # Metric-compatible fonts (Arial/Times)
      fira;
  };

  # Define the development shell
  shell = pkgs.mkShell {

    # Locale configuration for consistent behavior
    LOCALE_ARCHIVE = if pkgs.system == "x86_64-linux" then "${pkgs.glibcLocales}/lib/locale/locale-archive" else "";
    LANG = "en_US.UTF-8";
    LC_ALL = "en_US.UTF-8";
    LC_TIME = "en_US.UTF-8";
    LC_MONETARY = "en_US.UTF-8";
    LC_PAPER = "en_US.UTF-8";
    LC_MEASUREMENT = "en_US.UTF-8";

    # Fontconfig setup so Matplotlib can find fonts installed by Nix
    FONTCONFIG_FILE = "${pkgs.fontconfig.out}/etc/fonts/fonts.conf";

    shellHook = ''
      # 1. Configure font paths for Matplotlib and other tools
      export XDG_DATA_DIRS="${pkgs.dejavu_fonts}/share:${pkgs.freefont_ttf}/share:${pkgs.liberation_ttf}/share:$XDG_DATA_DIRS"
      fc-cache -f 2>/dev/null || true

      # 2. Add source directory to PYTHONPATH for immediate development
      #    This allows `import OlistProject` without installation
      export PYTHONPATH=$PWD/src:$PYTHONPATH
    '';

    # All packages that will be available inside the shell
    buildInputs = [ tex pyconf system_packages ];
  };
in
  {
    inherit pkgs shell;
  }
