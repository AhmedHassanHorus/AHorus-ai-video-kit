---
name: manim-animation
description: Programmatic mathematical, geometric, and technical explainer animations using Manim in Python. Use when generating animated diagrams, code blocks, neural network visualizations, and vector graphics.
---

# Manim Technical & Mathematical Explainer Animation Skill

This skill guides the agent in writing Python scripts using the **Manim** animation engine for technical, scientific, and geometric explainers.

## 1. Vertical 9:16 Short-Form Setup

Configure the camera in Python for vertical mobile video:

```python
from manim import *

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9.0
config.frame_height = 16.0
```

## 2. Best Explainer Scene Patterns

1. **Tech Diagrams & Networks:**
   * Use `Graph` or custom `Dot` + `Arrow` networks with glowing accents.
   * Animate flow of packets/data using `ShowPassingFlash(arrow)`.
2. **Code & Text Highlighting:**
   * Use `Code` object for syntax-highlighted snippets.
   * Highlight specific lines using `SurroundingRectangle(code[line_idx], color=YELLOW, buff=0.1)`.
3. **Data & Math Visuals:**
   * Use `Axes` and `FunctionGraph` with smooth curve transformations (`Transform(graph1, graph2)`).

## 3. Rendering Transparent Overlays

To output an animation with an alpha channel to overlay directly into FilmCraft:

```bash
manim -t -qh scene.py SceneName --format=webm
```
* `-t`: Transparent background.
* `-qh`: High quality (1080p).
* Output WebM with alpha can be imported into FilmCraft via `file.import` and placed on V2.
