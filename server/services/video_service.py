import os
import moviepy.editor as mpy

def resize_and_pad(clip, target_w, target_h):
    """Resizes a clip to fit target_h, pads width to target_w."""
    # Resize based on height, maintaining aspect ratio
    resized_clip = clip.resize(height=target_h)
    
    # Calculate padding needed
    padding_w = target_w - resized_clip.w
    left_pad = padding_w // 2
    right_pad = padding_w - left_pad
    
    # Apply padding only if needed
    if padding_w > 0:
        padded_clip = resized_clip.margin(left=left_pad, right=right_pad, color=(0,0,0))
    else:
        # If resizing made it wider (unlikely with height focus, but possible), crop
        padded_clip = resized_clip.crop(x_center=resized_clip.w/2, width=target_w)
        
    # Ensure the final size is exactly target_w x target_h
    # This guards against small rounding errors or unexpected resize behavior
    if padded_clip.w != target_w or padded_clip.h != target_h:
         padded_clip = padded_clip.resize(width=target_w, height=target_h) # Force resize if needed

    return padded_clip

def assemble_final_video(celebrity_video_path, visuals_path, output_dir):
    """
    Assembles the final video by stacking the visuals video on top of the 
    celebrity video, fitting them into a 1920x1080 frame.
    """
    print(f"Assembling final video from: {celebrity_video_path} and {visuals_path}")
    celeb_clip = None
    visuals_clip = None
    final_clip = None

    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Final output path
        final_path = os.path.join(output_dir, 'final_video.mp4')

        # Target dimensions
        target_w = 1920
        target_h = 1080
        clip_h = target_h // 2 # Height for each individual clip panel

        # Load clips
        print("Loading video clips...")
        celeb_clip = mpy.VideoFileClip(celebrity_video_path)
        visuals_clip = mpy.VideoFileClip(visuals_path)
        print("Clips loaded.")

        # Use celebrity video's duration as the master duration
        master_duration = celeb_clip.duration
        
        # Resize and pad clips to fit 1920x540, using master duration
        print("Resizing and padding clips...")
        celeb_processed = resize_and_pad(celeb_clip, target_w, clip_h).set_duration(master_duration)
        visuals_processed = resize_and_pad(visuals_clip, target_w, clip_h).set_duration(master_duration)
        print("Clips processed.")

        # Stack the clips vertically (visuals on top)
        print("Stacking clips...")
        final_clip = mpy.clips_array([[visuals_processed], [celeb_processed]])
        
        # Set the audio from the celebrity clip
        if celeb_clip.audio:
            print("Setting audio...")
            final_clip = final_clip.set_audio(celeb_clip.audio)
        else:
             print("Warning: Celebrity clip has no audio.")

        # Write the final video
        print(f"Writing final video to: {final_path}...")
        final_clip.write_videofile(
            final_path, 
            codec='libx264', 
            audio_codec='aac',
            threads=4, # Use multiple threads for faster encoding
            logger='bar' # Show progress bar
        )
        print("Final video written successfully.")
        
        return final_path

    except Exception as e:
        print(f"Error assembling video: {e}")
        # Consider re-raising or returning an error indicator
        raise # Re-raise the exception to signal failure in the Celery task

    finally:
        # Clean up resources
        print("Cleaning up video resources...")
        if celeb_clip:
            try:
                celeb_clip.close()
            except Exception as e:
                 print(f"Error closing celeb_clip: {e}")
        if visuals_clip:
             try:
                visuals_clip.close()
             except Exception as e:
                 print(f"Error closing visuals_clip: {e}")
        # Intermediate clips (processed) are usually handled by final_clip closure
        if final_clip:
            try:
                final_clip.close()
            except Exception as e:
                 print(f"Error closing final_clip: {e}")
        print("Cleanup complete.")
