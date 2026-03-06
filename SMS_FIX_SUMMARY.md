# SMS Fix Summary - Accident Detection System

## Issues Identified

### 1. Backend Bug: SMS Not Being Sent (FIXED ✅)
**Problem:** The `/trigger_alerts` endpoint in main.py was finding nearby users but NOT actually sending any SMS messages. The code just counted users but never called SMS functions.

**Solution Applied:**
- Updated `/trigger_alerts` endpoint in `main.py` to actually send SMS to:
  1. Victim's emergency contacts (family members)
  2. Nearby users within 5km radius
  3. Nearest police station
  4. Nearest hospital

### 2. Android App: Alarm Not Playing When Phone is Off
**Problem:** The alarm only plays using Android's `Ringtone` which doesn't work when:
- Phone is turned off
- Phone is in Doze mode (battery optimization)
- Screen is off and app is in background

**Solution Required (Android Side):**
The user needs to modify `EmergencyCountdownActivity.kt` to use `AlarmManager` with high-priority alarms:

```kotlin
// In EmergencyCountdownActivity.kt - Add this for system-level alarm

private fun scheduleSystemAlarm() {
    val alarmManager = getSystemService(Context.ALARM_SERVICE) as AlarmManager
    val intent = Intent(this, AlarmReceiver::class.java)
    val pendingIntent = PendingIntent.getBroadcast(
        this, 
        0, 
        intent, 
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
    )
    
    // Use setExactAndAllowWhileIdle for reliable alarm even in Doze mode
    alarmManager.setExactAndAllowWhileIdle(
        AlarmManager.RTC_WAKEUP,
        System.currentTimeMillis() + 30000, // 30 seconds
        pendingIntent
    )
}

// Create AlarmReceiver.kt broadcast receiver
class AlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        // Play loud alarm sound using MediaPlayer
        val mediaPlayer = MediaPlayer.create(context, R.raw.alarm_sound)
        mediaPlayer?.apply {
            isLooping = true
            start()
        }
    }
}
```

**AndroidManifest.xml additions:**
```xml
<receiver android:name=".AlarmReceiver" android:exported="false" />
<uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />
<uses-permission android:name="android.permission.USE_EXACT_ALARM" />
<uses-permission android:name="android.permission.WAKE_LOCK" />
```

### 3. Android App: Location Showing as 0,0
**Problem:** The GPS hasn't warmed up when requesting location, causing 0,0 coordinates to be sent.

**Solution Required (Android Side):**
Pass the last known good location from LocationService to EmergencyCountdownActivity:

```kotlin
// In LocationService.kt - store last known good location
private var lastKnownLocation: Location? = null

fun getLastKnownGoodLocation(): Location? = lastKnownLocation

// When location update is received
override fun onLocationResult(locationResult: LocationResult) {
    if (locationResult.lastLocation != null) {
        lastKnownLocation = locationResult.lastLocation
    }
}

// In MainActivity.kt - when starting EmergencyCountdownActivity
val lastLocation = locationService.getLastKnownGoodLocation()
val intent = Intent(this, EmergencyCountdownActivity::class.java).apply {
    putExtra("latitude", lastLocation?.latitude ?: 0.0)
    putExtra("longitude", lastLocation?.longitude ?: 0.0)
}
startActivity(intent)
```

## Summary of Changes Made

### Backend (main.py) - ✅ COMPLETED
1. Fixed `/trigger_alerts` endpoint to actually send SMS messages
2. Added SMS sending to:
   - Victim's emergency contacts
   - Nearby users
   - Police stations
   - Hospitals
3. Added proper logging for debugging

### Android App - Requires User Implementation
1. Use AlarmManager for system-level alarms (works when phone is off)
2. Pass last known good GPS location to prevent 0,0 coordinates
3. Add the "name" field to the backend JSON payload as mentioned earlier

## Testing the Fix

1. **Backend Test:**
   POST /trigger_alerts
   {
     "accidentId": "ACCIDENT_ID_HERE"
   }

2. **SMS Diagnostic:**
   GET /diagnose_sms

3. **Test SMS:**
   GET /test_sms/+919999999999

## Notes

- Make sure Twilio credentials are properly set in Render.com environment variables
- Ensure Firebase has emergency contacts stored for users
- The Android app must send userId when reporting accident so the backend can find emergency contacts

