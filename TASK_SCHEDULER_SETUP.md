# Task Scheduler Setup Instructions

## Fix for "Operator or Administrator Refused Request" Error

This error occurs when Task Scheduler doesn't have proper permissions. Follow these steps:

### Step 1: Create the Scheduled Task

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Basic Task** in the right panel
3. Name: `YouTube Shorts Automation - Morning`
4. Description: `Generates and uploads YouTube Shorts at 8 AM`
5. Click **Next**

### Step 2: Set Trigger

1. Select **Daily**
2. Start time: **08:00:00**
3. Recur every: **1 days**
4. Click **Next**

### Step 3: Set Action

1. Select **Start a program**
2. Program/script: `C:\Windows\System32\cmd.exe`
3. Add arguments: `/c "cd /d C:\Users\Acer\Desktop\quotes-shorts-automation && run.bat"`
4. Click **Next**, then **Finish**

### Step 4: Configure Advanced Settings (CRITICAL)

1. Right-click the task you just created → **Properties**
2. Go to the **General** tab:
   - ✅ Check **Run whether user is logged on or not**
   - ✅ Check **Run with highest privileges**
   - ✅ Check **Hidden** (optional)
3. Go to the **Conditions** tab:
   - ❌ Uncheck **Start the task only if the computer is on AC power**
   - ❌ Uncheck **Stop if the computer switches to battery power**
4. Go to the **Settings** tab:
   - ✅ Check **Allow task to be run on demand**
   - ✅ Check **Run task as soon as possible after a scheduled start is missed**
   - Set **If the task fails, restart every**: `10 minutes`
   - Set **Attempt to restart up to**: `3 times`
5. Click **OK**
6. Enter your Windows password when prompted

### Step 5: Create Second Task for Evening

Repeat Steps 1-4 with these changes:
- Name: `YouTube Shorts Automation - Evening`
- Start time: **19:00:00** (7 PM)

### Step 6: Test the Task

1. Right-click the task → **Run**
2. Check `automation.log` for output
3. Verify video was generated in `assets/output/`

## Troubleshooting

### If task still fails:
1. Check `automation.log` for error messages
2. Ensure Python is in system PATH (not just user PATH)
3. Run `python --version` in Command Prompt to verify
4. Make sure Ollama is set to start automatically (or always running)

### If duplicate videos are uploaded:
- This is now fixed - each run generates a unique quote with random seed
- Check the logs to confirm different quotes are being generated
