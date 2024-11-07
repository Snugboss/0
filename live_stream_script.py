
# Keep-alive code (for Google Colab)
from IPython.display import Javascript

js_code = """
function ClickConnect(){
    console.log("Working");
    document.querySelector("colab-connect-button").click()
}
setInterval(ClickConnect, 60000)
"""

display(Javascript(js_code))

# Required imports
!pip install requests

# Streaming code
import subprocess
import time
import logging
from datetime import datetime
import requests
import signal
import sys
from threading import Thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stream_log.txt'),
        logging.StreamHandler()
    ]
)

class LoopingStreamManager:
    def __init__(self):
        self.youtube_stream_key = "t5jb-44zm-319x-0y4e-b1j8"  # Replace with your YouTube stream key
        self.video_paths = [  # List of video paths or URLs
            "https://hanuman.s3.us-south.cloud-object-storage.appdomain.cloud/0000.mp4",
            "https://hanuman.s3.us-south.cloud-object-storage.appdomain.cloud/0001.mp4",
            "https://hanuman.s3.us-south.cloud-object-storage.appdomain.cloud/0002.mp4",
        ]
        self.current_process = None
        self.is_running = True
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        logging.info("Received shutdown signal. Cleaning up...")
        self.is_running = False
        if self.current_process:
            self.current_process.terminate()
        sys.exit(0)

    def check_internet_connection(self):
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.RequestException:
            return False

    def stream_video(self, video_path):
        logging.info(f"Starting live stream for: {video_path}")
        ffmpeg_command = [
            'ffmpeg',
            '-re',
            '-i', video_path,
            '-c:v', 'libx264',
            '-preset', 'veryfast',
            '-b:v', '3000k',
            '-maxrate', '3000k',
            '-bufsize', '6000k',
            '-pix_fmt', 'yuv420p',
            '-g', '50',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '44100',
            '-f', 'flv',
            f'rtmp://a.rtmp.youtube.com/live2/{self.youtube_stream_key}'
        ]

        try:
            self.current_process = subprocess.Popen(
                ffmpeg_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.current_process.wait()
        except Exception as e:
            logging.error(f"Error streaming video: {str(e)}")
            return False
        return True

    def run_stream_loop(self):
        while self.is_running:
            if not self.check_internet_connection():
                logging.warning("No internet connection. Retrying in 30 seconds...")
                time.sleep(30)
                continue

            for video_path in self.video_paths:
                if not self.is_running:
                    break
                success = self.stream_video(video_path)
                if not success:
                    logging.warning(f"Streaming failed for {video_path}. Retrying next video...")
                    time.sleep(10)

                logging.info(f"Completed streaming for {video_path}")
                time.sleep(5)

    def start(self):
        logging.info("Starting 24/7 live stream...")
        stream_thread = Thread(target=self.run_stream_loop)
        stream_thread.daemon = True
        stream_thread.start()

        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.handle_shutdown(None, None)

if __name__ == "__main__":
    manager = LoopingStreamManager()
    manager.start()
