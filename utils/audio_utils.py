import base64
import os
import uuid

def decode_audio_base64(base64_string: str, output_dir: str = "/tmp") -> str:
    """Decodes base64 string to an mp3 file in the specified directory."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(output_dir, f"{file_id}.mp3")
    
    try:
        # Some base64 strings might include headers like "data:audio/mp3;base64,"
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
            
        audio_data = base64.b64decode(base64_string)
        with open(file_path, "wb") as f:
            f.write(audio_data)
        return file_path
    except Exception as e:
        raise ValueError(f"Error decoding base64 audio: {e}")

def cleanup_file(file_path: str):
    """Deletes a file from the disk."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning up file {file_path}: {e}")
