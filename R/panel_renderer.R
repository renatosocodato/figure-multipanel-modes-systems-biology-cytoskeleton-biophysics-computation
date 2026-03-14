#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
  library(yaml)
  library(jsonlite)
  library(dplyr)
  library(readr)
})

is_nullish <- function(value) {
  is.null(value) || (length(value) == 1 && is.na(value))
}

coalesce <- function(...) {
  values <- list(...)
  for (value in values) {
    if (!is_nullish(value)) {
      return(value)
    }
  }
  return(NULL)
}

normalize_chart_type <- function(chart_type) {
  chart_type <- tolower(coalesce(chart_type, "bar"))
  chart_type <- gsub("-", "_", chart_type, fixed = TRUE)
  replacements <- c(
    histogram = "hist",
    boxplot = "box",
    qq_plot = "qq",
    "precision_recall" = "precision_recall",
    "precision-recall" = "precision_recall"
  )
  if (chart_type %in% names(replacements)) {
    return(replacements[[chart_type]])
  }
  chart_type
}

normalize_formats <- function(formats) {
  out <- c("pdf", "png")
  if (is.null(formats)) {
    return(out)
  }
  requested <- tolower(formats)
  for (fmt in requested) {
    if (fmt %in% c("pdf", "png", "svg", "tiff", "jpg", "jpeg")) {
      if (fmt == "jpg") {
        fmt <- "jpeg"
      }
      if (!(fmt %in% out)) {
        out <- c(out, fmt)
      }
    }
  }
  return(out)
}

safe_data <- function(path, fmt) {
  if (!file.exists(path)) {
    return(data.frame(x = 1:5, y = c(1, 2, 1.5, 3.2, 2.8), group = rep(c("A", "B"), length.out = 5)))
  }
  fmt <- tolower(coalesce(fmt, "auto"))
  if (fmt %in% c("tsv", "tab")) {
    return(read_tsv(path, show_col_types = FALSE))
  }
  if (fmt == "json") {
    return(fromJSON(path, simplifyDataFrame = TRUE))
  }
  if (fmt == "rds") {
    return(readRDS(path))
  }
  if (fmt == "feather" && requireNamespace("arrow", quietly = TRUE)) {
    return(arrow::read_feather(path))
  }
  if (fmt == "parquet" && requireNamespace("arrow", quietly = TRUE)) {
    return(arrow::read_parquet(path))
  }
  if (fmt == "npy") {
    stop("NPY input is unsupported in R renderer.")
  }
  tryCatch(read_csv(path, show_col_types = FALSE), error = function(...) read_tsv(path, show_col_types = FALSE))
}

minimal_theme <- function() {
  theme_minimal(base_family = "Arial", base_size = 10) +
    theme(
      plot.title = element_text(face = "bold", size = 12, colour = "#111827"),
      plot.subtitle = element_text(size = 9.5, colour = "#374151"),
      axis.title = element_text(size = 9.5),
      panel.grid.major = element_line(color = "#E5E7EB", linewidth = 0.25),
      panel.grid.minor = element_blank(),
      panel.border = element_blank(),
      axis.ticks = element_line(color = "#9CA3AF", size = 0.3),
      legend.position = "none"
    )
}

infer_mappings <- function(chart, data) {
  mappings <- coalesce(chart$mappings, list())
  columns <- names(data)
  lower <- tolower(columns)
  pick_by_rules <- function(rule) {
    idx <- which(vapply(lower, function(x) grepl(rule, x, fixed = TRUE), logical(1L)))
    if (length(idx) == 0L) {
      return(NULL)
    }
    columns[[idx[1L]]]
  }
  if (is.null(mappings$x)) mappings$x <- coalesce(pick_by_rules("x"), if (length(columns) > 0) columns[[1]] else NULL)
  if (is.null(mappings$y)) mappings$y <- coalesce(pick_by_rules("y"), pick_by_rules("value"), if (length(columns) > 1) columns[[2]] else columns[[1]], "y")
  if (is.null(mappings$group) && "group" %in% columns) mappings$group <- "group"
  if (is.null(mappings$category) && "category" %in% columns) mappings$category <- "category"
  if (is.null(mappings$category) && "class" %in% columns) mappings$category <- "class"
  mappings
}

add_tile <- function(p, panel_label, title, subtitle, status) {
  label <- coalesce(panel_label, "panel")
  subtitle_text <- paste0("[", label, "] ", coalesce(title, "Panel"), ifelse(is.null(subtitle) || is.na(subtitle) || subtitle == "", "", paste0(" — ", subtitle)))
  if (!is.null(status) && !is.na(status) && nzchar(status)) {
    subtitle_text <- paste0(subtitle_text, " | ", status)
  }
  p + annotate("text", x = -Inf, y = Inf, hjust = -0.02, vjust = 1.35, size = 3.1, family = "Arial", fontface = "bold", label = subtitle_text, color = "#111827")
}

safe_numeric <- function(values) {
  as.numeric(as.character(values))
}

heat_matrix_plot <- function(data, title, subtitle, fill = NULL) {
  if (is.null(fill)) fill <- "value"
  if (nrow(data) == 0L || ncol(data) < 2L) {
    return(ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No numeric input") + theme_void())
  }
  ggplot(data, aes_string(x = "Var1", y = "Var2", fill = fill)) +
    geom_tile() +
    scale_fill_viridis_c(option = "A") +
    labs(title = title, subtitle = subtitle) +
    minimal_theme()
}

render_chart <- function(chart, data, title, subtitle, tile_label, status) {
  mappings <- infer_mappings(chart, data)
  ctype <- normalize_chart_type(coalesce(chart$chart_type, chart$type))
  opts <- coalesce(chart$options, list())
  palette <- c("#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#EECA3B")

  p <- switch(
    ctype,
    bar = {
      base <- ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]]))
      if (!is.null(mappings$group) && mappings$group %in% names(data)) {
        base + geom_col(aes(fill = .data[[mappings$group]]), show.legend = FALSE)
      } else {
        base + geom_col(fill = palette[[1]], show.legend = FALSE)
      }
    },
    lollipop = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) +
        geom_segment(aes(xend = .data[[mappings$x]], y = 0, yend = .data[[mappings$y]]), color = palette[[1]]) +
        geom_point(color = palette[[1]], size = 1.8)
    },
    hist = {
      ggplot(data, aes(.data[[mappings$x]])) + geom_histogram(fill = palette[[1]], bins = as.integer(coalesce(opts$bins, 30)), alpha = 0.8)
    },
    kde = {
      ggplot(data, aes(.data[[mappings$x]])) + geom_density(fill = palette[[1]], alpha = 0.45)
    },
    ecdf = {
      ggplot(data, aes(.data[[mappings$x]])) + stat_ecdf()
    },
    box = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_boxplot(fill = palette[[1]])
    },
    violin = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_violin(fill = palette[[1]], alpha = 0.7)
    },
    dot = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) +
        geom_point(color = palette[[1]], alpha = 0.8, size = 1.4)
    },
    dot_plot = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) +
        geom_jitter(color = palette[[1]], alpha = 0.8, size = 1.4)
    },
    scatter = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) +
        geom_point(color = palette[[1]], alpha = 0.8, size = 1.2)
    },
    line = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_line(color = palette[[1]], linewidth = 0.9)
    },
    area = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_area(fill = palette[[1]], alpha = 0.35) + geom_line(color = palette[[1]], linewidth = 0.9)
    },
    stacked_area = {
      if (!is.null(mappings$group) && mappings$group %in% names(data)) {
        ggplot(data, aes(.data[[mappings$x]], fill = .data[[mappings$group]], y = .data[[mappings$y]])) + geom_area(alpha = 0.9)
      } else {
        ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_area(fill = palette[[1]], alpha = 0.35)
      }
    },
    regression = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) +
        geom_point(color = palette[[1]], alpha = 0.7) +
        geom_smooth(method = "lm", se = TRUE, color = palette[[2]])
    },
    regression_ci = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) +
        geom_point(color = palette[[1]], alpha = 0.7) +
        geom_smooth(method = "lm", se = TRUE, color = palette[[2]])
    },
    hexbin = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_hex()
    },
    correlogram = {
      num <- dplyr::select_if(data, is.numeric)
      if (ncol(num) <= 1L) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "Need >=2 numeric columns")
      } else {
        corr <- stats::cor(num, use = "pairwise.complete.obs")
        if (requireNamespace("reshape2", quietly = TRUE)) {
          melted <- reshape2::melt(corr)
          heat_matrix_plot(melted, title, subtitle, fill = "value")
        } else {
          ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "Install reshape2 for correlogram export")
        }
      }
    },
    heatmap = {
      num <- dplyr::select_if(data, is.numeric)
      if (ncol(num) == 0L) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No numeric input")
      } else {
        corr <- stats::cor(num, use = "pairwise.complete.obs")
        melted <- if (requireNamespace("reshape2", quietly = TRUE)) reshape2::melt(corr) else data.frame(Var1 = integer(), Var2 = integer(), value = numeric())
        if (nrow(melted) == 0L) {
          ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No numeric input")
        } else {
          heat_matrix_plot(melted, title, subtitle, fill = "value")
        }
      }
    },
    corr_matrix = {
      num <- dplyr::select_if(data, is.numeric)
      if (ncol(num) == 0L) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No numeric input")
      } else {
        corr <- stats::cor(num, use = "pairwise.complete.obs")
        melted <- if (requireNamespace("reshape2", quietly = TRUE)) reshape2::melt(corr) else data.frame(Var1 = integer(), Var2 = integer(), value = numeric())
        if (nrow(melted) == 0L) {
          ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No numeric input")
        } else {
          ggplot(melted, aes(Var1, Var2, fill = value)) +
            geom_tile() +
            scale_fill_gradient2(low = "#2166ac", high = "#b2182b", mid = "#f7f7f7", midpoint = 0) +
            labs(title = title, subtitle = subtitle) + minimal_theme()
        }
      }
    },
    pca = {
      num <- dplyr::select_if(data, is.numeric)
      if (ncol(num) < 2L) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "Not enough numeric columns for PCA")
      } else {
        pca <- stats::prcomp(num, scale. = TRUE)
        scores <- as.data.frame(pca$x[, 1:2])
        names(scores)[1:2] <- c("PC1", "PC2")
        ggplot(scores, aes(PC1, PC2)) + geom_point(color = palette[[1]], alpha = 0.8, size = 1.2) + labs(title = title, subtitle = subtitle)
      }
    },
    pca_scatter = {
      ggplot2::ggplot(data = data.frame(x = 1, y = 1), mapping = aes(x, y)) + geom_text(label = "pca_scatter unavailable in base renderer")
    },
    tsne = {
      ggplot2::ggplot(mapping = aes(1, 1)) + geom_text(label = "tsne unavailable in base renderer", x = 1, y = 1)
    },
    tsne_scatter = {
      ggplot2::ggplot(mapping = aes(1, 1)) + geom_text(label = "tsne_scatter unavailable in base renderer", x = 1, y = 1)
    },
    umap = {
      ggplot2::ggplot(mapping = aes(1, 1)) + geom_text(label = "umap unavailable in base renderer", x = 1, y = 1)
    },
    umap_scatter = {
      ggplot2::ggplot(mapping = aes(1, 1)) + geom_text(label = "umap_scatter unavailable in base renderer", x = 1, y = 1)
    },
    stacked_bar = {
      category <- coalesce(mappings$category, mappings$x)
      if (is.null(category) || !category %in% names(data)) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No category mapping")
      } else {
        base <- ggplot(data, aes_string(x = category, weight = mappings$y))
        if (!is.null(mappings$group) && mappings$group %in% names(data)) {
          base <- base + aes_string(fill = mappings$group)
          geom <- geom_bar()
        } else {
          geom <- geom_bar(fill = palette[[1]])
        }
        base + geom
      }
    },
    stacked_bar_100 = {
      category <- coalesce(mappings$category, mappings$x)
      if (is.null(category) || !category %in% names(data)) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No category mapping")
      } else {
        base <- ggplot(data, aes_string(x = category, y = mappings$y))
        if (!is.null(mappings$group) && mappings$group %in% names(data)) {
          base <- base + aes_string(fill = mappings$group)
          base + geom_bar(position = "fill")
        } else {
          base + geom_bar(position = "fill", fill = palette[[1]])
        }
      }
    },
    outcome_composition = {
      category <- coalesce(mappings$category, mappings$x)
      if (is.null(category) || !category %in% names(data)) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No category mapping")
      } else {
        ggplot(data, aes(.data[[category]])) + geom_bar(fill = palette[[1]], alpha = 0.85)
      }
    },
    tally_tiles = {
      category <- coalesce(mappings$category, mappings$x)
      if (is.null(category) || !category %in% names(data)) {
        ggplot(data.frame(x = 1, y = 1), aes(x, y)) + geom_text(label = "No category mapping")
      } else {
        counts <- as.data.frame(table(data[[category]], useNA = "ifany"))
        names(counts) <- c("tile", "count")
        ggplot(counts, aes(tile, count, fill = tile)) + geom_tile() + scale_fill_viridis_d()
      }
    },
    roc = {
      ggplot(data.frame(x = c(0, 1), y = c(0, 1)), aes(x, y)) + geom_line(color = palette[[1]]) + geom_abline(linetype = "dashed", color = "#6B7280")
    },
    pr = { ggplot(data.frame(x = c(0, 1), y = c(1, 0)), aes(x, y)) + geom_line(color = palette[[1]]) },
    precision_recall = { ggplot(data.frame(x = c(0, 1), y = c(1, 0)), aes(x, y)) + geom_line(color = palette[[1]]) },
    calibration = { ggplot(data.frame(x = c(0, 1), y = c(0, 1)), aes(x, y)) + geom_abline(color = "#6B7280") },
    residuals = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_point(color = palette[[1]], alpha = 0.75, size = 1.2)
    },
    qq = {
      ggplot(data, aes(sample = safe_numeric(data[[mappings$x]]))) + stat_qq() + stat_qq_line()
    },
    ma = {
      ggplot(data, aes(.data[[mappings$x]], .data[[mappings$y]])) + geom_point(color = palette[[1]])
    },
    volcano = {
      ggplot(data, aes(.data[[mappings$x]], -.data[[mappings$y]])) + geom_point(color = palette[[1]])
    },
    manhattan = {
      ggplot(data, aes(seq_len(nrow(data)), -.safe_numeric(data[[mappings$y]]))) + geom_point(color = palette[[1]], size = 1.2)
    },
    {
      ggplot(data, aes(1, 1)) + geom_text(label = paste("Unsupported chart type:", ctype))
    }
  )

  p <- p + labs(title = title, subtitle = subtitle) + minimal_theme()
  add_tile(p, tile_label, title, subtitle, status)
}

render_single_panel <- function(panel_spec, out_dir, dpi) {
  chart <- panel_spec$chart
  data <- safe_data(chart$data$path, chart$data$format)
  title <- coalesce(panel_spec$title, panel_spec$label)
  subtitle <- coalesce(panel_spec$subtitle, "")
  panel_label <- coalesce(panel_spec$tile$label, panel_spec$label)
  status <- coalesce(panel_spec$tile$status, coalesce(panel_spec$tile$outcome, "pass"))
  plot <- render_chart(chart, data, title, subtitle, panel_label, status)

  base <- coalesce(panel_spec$output_name, panel_spec$label)
  formats <- normalize_formats(coalesce(panel_spec$rendered_formats, panel_spec$render$formats))
  if (length(formats) == 0L) formats <- c("pdf", "png")

  out <- list()
  for (fmt in formats) {
    file <- file.path(out_dir, paste0(base, ".", fmt))
    if (fmt == "pdf") {
      ggsave(file, plot, width = 8, height = 6, device = cairo_pdf)
    } else if (fmt == "svg") {
      ggsave(file, plot, width = 8, height = 6)
    } else if (fmt == "jpeg") {
      ggsave(file, plot, width = 8, height = 6, dpi = dpi, device = "jpeg")
    } else if (fmt == "tiff") {
      ggsave(file, plot, width = 8, height = 6, dpi = dpi, device = "tiff")
    } else {
      ggsave(file, plot, width = 8, height = 6, dpi = dpi, device = "png")
    }
    out[[fmt]] <- file
  }
  out
}

render_figure_from_spec <- function(spec_path, out_dir = NULL) {
  raw <- yaml::read_yaml(spec_path)
  if (is.null(raw)) {
    stop("Unable to read spec")
  }
  if (!is.null(raw$palette)) {
    if (!is.null(raw$palette$source) && tolower(raw$palette$source) != "colorbrewer") {
      message("R renderer currently implements ColorBrewer-compatible defaults.")
    }
  }
  output_dir <- if (!is.null(out_dir) && nzchar(out_dir)) out_dir else file.path(dirname(spec_path), coalesce(raw$prefix, "figure"))
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  dpi <- coalesce(raw$render$dpi, 600)

  outputs <- lapply(raw$panels, function(panel) {
    render_single_panel(panel, output_dir, dpi = coalesce(dpi, 600))
  })

  out <- list(
    outputs = outputs,
    figure = file.path(output_dir, paste0(coalesce(raw$prefix, "figure"), ".pdf")),
    png = file.path(output_dir, paste0(coalesce(raw$prefix, "figure"), ".png"))
  )
  saveRDS(out, file.path(output_dir, "panel_renderer_outputs.rds"), version = 3)
  invisible(out)
}

if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) < 1L) {
    stop("Usage: Rscript panel_renderer.R <spec.yaml> [output_dir]")
  }
  render_figure_from_spec(args[[1L]], if (length(args) >= 2L) args[[2L]] else NULL)
}
