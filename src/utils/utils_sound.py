"""Python module to make beeping sound to alert when it finishes running.

For example in a Jupyter cell, or in a script.
"""

from IPython.display import Audio, display
import numpy as np


def beep() -> None:
    # Generate a 1 second sine wave at 440Hz
    sample_rate = 44100
    t = np.linspace(0, 1, sample_rate, False)
    tone = np.sin(440 * 2 * np.pi * t)

    # Ensure that highest value is in 16-bit range
    audio = Audio(tone, rate=sample_rate, autoplay=True)
    display(audio)
    print("Beep completed!")
