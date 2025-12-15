# Stable Diffusion Setup Guide

## Do NOT Move the Folder

**Answer:** No, keep Stable Diffusion on your Desktop. Do NOT move it to the quotes-shorts-automation folder.

## How to Set Up Stable Diffusion

### Step 1: Locate Your Stable Diffusion Folder

You mentioned it's on your Desktop. It's probably named something like:
- `stable-diffusion-webui`
- `AUTOMATIC1111`
- `stable-diffusion`

### Step 2: Start Stable Diffusion with API Enabled

1. **Find the launch file** in your Stable Diffusion folder:
   - `webui-user.bat` (Windows)

2. **Edit `webui-user.bat`:**
   - Right-click → Edit
   - Find the line that says `set COMMANDLINE_ARGS=`
   - Change it to: `set COMMANDLINE_ARGS=--api`
   - Save and close

3. **Launch Stable Diffusion:**
   - Double-click `webui-user.bat`
   - Wait for it to start (first time takes 5-10 minutes)
   - You'll see: `Running on local URL: http://127.0.0.1:7860`

4. **Keep it running** while generating videos

### Step 3: Verify It's Working

Open a browser and go to: http://127.0.0.1:7860

You should see the Stable Diffusion web interface.

## Alternative: Use Fallback Images (Current Setup)

**Good news:** The system already works WITHOUT Stable Diffusion!

When SD is not running, it automatically generates gradient backgrounds. This is what's happening now:
```
WARNING:Main:Stable Diffusion is not running. Will use fallback gradient generator.
```

The videos will still work, just with simpler backgrounds instead of AI-generated images.

## Recommendation

For now, **skip Stable Diffusion** and focus on getting quotes working:

1. ✅ Ollama is installed (mistral model ready)
2. ⏳ Fix the timeout issue (increased to 120s)
3. ✅ Fallback images work fine
4. 🎯 Get the automation running first

You can add Stable Diffusion later for better images.

## If You Want to Use Stable Diffusion Later

1. Edit `webui-user.bat` to add `--api`
2. Run it before running the automation
3. The system will automatically detect it and use AI images instead of gradients

That's it! No need to move folders or change paths.
