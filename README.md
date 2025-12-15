# Crochet Pattern Analyzer

A computer vision application that analyzes images of crochet pieces to extract pattern details, including stitch counts, yarn flow, and directionality.

## Features

*   **Hue Isolation**: Automatically masks yarn based on color selection.
*   **Yarn Framing**: Detects the "spine" and width of the yarn structure.
*   **Stitch Detection**: Counts individual stitches using distance transform and corner detection algorithms.
*   **Directionality**: Determines the flow of the crochet pattern (Left/Right/Up/Down).
*   **Visual Debugging**: Step-by-step pipeline viewer to inspect the analysis process.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the main application:

```bash
python main.py
```

1.  **Load Image**: Select an image file.
2.  **Isolate**: Click on the yarn to isolate it from the background.
3.  **Analyze**: Run the full detection pipeline.
4.  **View Steps**: Use the "View Steps" button to see how the algorithm processed the image.

## Project Structure

*   `main.py`: Entry point.
*   `gui/`: Application interface and logic.
*   `preprocessing/`: Image filters and color isolation.
*   `postprocessing/`: Core analysis algorithms (spine, stitches, direction).