"""Gradio demo app."""
import math

import gradio as gr


def compute_b():
    return math.pi / (4 * math.pi**2 + 2 * math.pi * math.sqrt(3))

demo = gr.Interface(fn=compute_b, inputs=[], outputs="text",
                     title="Research Papers Verification")
if __name__ == "__main__":
    demo.launch()
