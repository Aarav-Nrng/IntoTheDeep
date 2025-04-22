import pygame
import threading
import queue
import time
from pathlib import Path

class MinimalSoundManager:
    """
    A highly simplified sound manager that runs in a separate thread and
    can be completely bypassed if sound is causing performance issues.
    """
    def __init__(self):
        self.enabled = False
        self.initialized = False
        self.sound_queue = queue.Queue()
        self.sounds = {}
        self.running = True
        self.sound_thread = None
    
    def initialize(self):
        """Only initialize mixer when explicitly requested"""
        if self.initialized:
            return True
            
        try:
            # Initialize with conservative buffer size and lower frequency
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=1024)
            self.initialized = True
            
            # Start the sound thread only after successful initialization
            self.sound_thread = threading.Thread(target=self._sound_worker, daemon=True)
            self.sound_thread.start()
            
            return True
        except Exception as e:
            print(f"Sound system initialization failed: {e}")
            self.enabled = False
            return False
    
    def enable(self):
        """Enable the sound system"""
        if not self.initialized:
            success = self.initialize()
            if not success:
                return False
        self.enabled = True
        return True
    
    def disable(self):
        """Disable the sound system"""
        self.enabled = False
    
    def _sound_worker(self):
        """Background thread for processing sound requests"""
        while self.running:
            try:
                # Short timeout to allow checking if thread should exit
                sound_request = self.sound_queue.get(timeout=0.1)
                
                if not self.enabled:
                    # Skip processing if sounds are disabled
                    self.sound_queue.task_done()
                    continue
                
                action = sound_request.get("action", "")
                
                if action == "play":
                    sound = sound_request.get("sound")
                    if sound:
                        try:
                            sound.play()
                        except:
                            # Ignore all errors in sound playback
                            pass
                
                elif action == "music_play":
                    music_file = sound_request.get("file")
                    volume = sound_request.get("volume", 0.3)
                    
                    try:
                        pygame.mixer.music.load(music_file)
                        pygame.mixer.music.set_volume(volume)
                        pygame.mixer.music.play(-1)
                    except:
                        # Ignore all errors in music playback
                        pass
                
                elif action == "music_stop":
                    try:
                        pygame.mixer.music.stop()
                    except:
                        pass
                
                elif action == "music_pause":
                    try:
                        pygame.mixer.music.pause()
                    except:
                        pass
                
                elif action == "music_unpause":
                    try:
                        pygame.mixer.music.unpause()
                    except:
                        pass
                
                self.sound_queue.task_done()
                
            except queue.Empty:
                # No sound requests, just continue
                pass
            except Exception as e:
                # Catch and ignore all exceptions to keep thread running
                pass
            
            time.sleep(0.01)  # Small delay to prevent CPU hogging
    
    def load_sound(self, file_path, volume=0.3):
        """Load a sound file, or return None if sound system is disabled"""
        if not self.enabled or not self.initialized:
            return None
            
        try:
            if file_path in self.sounds:
                return self.sounds[file_path]
                
            sound = pygame.mixer.Sound(file_path)
            sound.set_volume(volume)
            self.sounds[file_path] = sound
            return sound
        except Exception as e:
            print(f"Error loading sound {file_path}: {e}")
            return None
    
    def play_sound(self, sound):
        """Queue a sound to be played in the background thread"""
        if not self.enabled or sound is None:
            return
            
        self.sound_queue.put({
            "action": "play",
            "sound": sound
        })
    
    def play_music(self, music_file, volume=0.3):
        """Queue music to play in the background thread"""
        if not self.enabled:
            return
            
        self.sound_queue.put({
            "action": "music_play",
            "file": music_file,
            "volume": volume
        })
    
    def stop_music(self):
        """Stop the current music"""
        if not self.enabled:
            return
            
        self.sound_queue.put({
            "action": "music_stop"
        })
    
    def pause_music(self):
        """Pause the current music"""
        if not self.enabled:
            return
            
        self.sound_queue.put({
            "action": "music_pause"
        })
    
    def unpause_music(self):
        """Unpause the current music"""
        if not self.enabled:
            return
            
        self.sound_queue.put({
            "action": "music_unpause"
        })
    
    def shutdown(self):
        """Clean up sound system resources"""
        self.running = False
        self.enabled = False
        
        if self.sound_thread and self.sound_thread.is_alive():
            self.sound_thread.join(timeout=0.5)
        
        self.sounds.clear()
        
        if self.initialized:
            try:
                pygame.mixer.quit()
            except:
                pass 