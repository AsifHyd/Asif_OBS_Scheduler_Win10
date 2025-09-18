import obsws_python as obs
import os

def test_obs_step_by_step():
    """Test each OBS operation step by step"""
    try:
        print("🔗 Step 1: Connecting to OBS...")
        client = obs.ReqClient(host='localhost', port=4444, password='', timeout=3)
        
        version = client.get_version()
        print(f"✅ Connected to OBS {version.obs_version}")
        
        print("\n🎬 Step 2: Testing scene creation...")
        test_scene_name = "DEBUG_TEST_SCENE"
        
        try:
            client.create_scene(test_scene_name)
            print(f"✅ Scene '{test_scene_name}' created successfully")
        except Exception as e:
            print(f"❌ Scene creation failed: {e}")
            client.disconnect()
            return False
        
        print("\n📝 Step 3: Testing text input creation...")
        try:
            client.create_input(
                input_name="DEBUG_TEXT",
                input_kind="text_gdiplus_v2",
                input_settings={
                    "text": "TEST - IT WORKS!",
                    "font": {"face": "Arial", "size": 48},
                    "color": 4294967295
                }
            )
            print("✅ Text input created successfully")
        except Exception as e:
            print(f"❌ Text input creation failed: {e}")
        
        print("\n🎯 Step 4: Testing adding input to scene...")
        try:
            client.create_scene_item(
                scene_name=test_scene_name,
                source_name="DEBUG_TEXT"
            )
            print("✅ Text added to scene successfully")
        except Exception as e:
            print(f"❌ Adding input to scene failed: {e}")
        
        print("\n🎥 Step 5: Testing video file...")
        # UPDATE THIS PATH to a real video file on your system
        test_video_path = r"C:\path\to\your\video.mp4"  # <-- CHANGE THIS!
        
        if os.path.exists(test_video_path):
            try:
                file_path = os.path.abspath(test_video_path).replace('\\', '/')
                print(f"Using video: {file_path}")
                
                client.create_input(
                    input_name="DEBUG_VIDEO",
                    input_kind="ffmpeg_source",
                    input_settings={
                        "local_file": file_path,
                        "is_local_file": True,
                        "looping": False,
                        "restart_on_activate": True
                    }
                )
                print("✅ Video input created successfully")
                
                client.create_scene_item(
                    scene_name=test_scene_name,
                    source_name="DEBUG_VIDEO"
                )
                print("✅ Video added to scene successfully")
                
            except Exception as e:
                print(f"❌ Video input failed: {e}")
        else:
            print(f"⚠️ Test video not found: {test_video_path}")
            print("   Update the test_video_path variable with a real video file")
        
        print(f"\n🎉 Test completed! Check OBS for scene: {test_scene_name}")
        
        # Switch to the test scene
        try:
            client.set_current_program_scene(test_scene_name)
            print(f"✅ Switched to test scene")
        except Exception as e:
            print(f"❌ Scene switching failed: {e}")
        
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Connection to OBS failed: {e}")
        return False

if __name__ == "__main__":
    test_obs_step_by_step()
