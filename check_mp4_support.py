import gradio as gr
import os

def check_video_playback(video_path):
    if video_path is None:
        return "No video uploaded", None
    
    # Get basic file info
    file_size = os.path.getsize(video_path) / (1024 * 1024)
    info = f"Video Path: {video_path}\nSize: {file_size:.2f} MB"
    print(f"Testing video: {video_path}")
    
    # Return the path. Gradio will attempt to serve this file directly to the browser.
    # If the browser supports the codec (e.g., H.264), it should play.
    return info, video_path

with gr.Blocks() as demo:
    gr.Markdown("## MP4 Browser Compatibility Test")
    gr.Markdown("Upload an MP4 file below. If it plays in the **Output Playback** box after clicking 'Check', your browser and Gradio support this specific MP4 file.")
    
    with gr.Row():
        with gr.Column():
            inp = gr.Video(label="Input MP4", format="mp4")
            btn = gr.Button("Check Playback", variant="primary")
        with gr.Column():
            out_info = gr.Textbox(label="Debug Info")
            out_vid = gr.Video(label="Output Playback")
    
    btn.click(fn=check_video_playback, inputs=inp, outputs=[out_info, out_vid])

if __name__ == "__main__":
    print("Launching MP4 test... Open the URL displayed below in your browser.")
    demo.launch()