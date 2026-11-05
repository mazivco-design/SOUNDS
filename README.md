# sounds

מפעל קולות מרכזי לכל האפליקציות, עם ElevenLabs.

- לכל אפליקציה יש תיקייה: `projects/<שם האפליקציה>/list.json`. זו רשימת הקולות שצריך לייצר.
- הפעולה **eleven-audio** (בלשונית Actions → Run workflow) מייצרת רק קבצים שעוד לא קיימים, ושומרת אותם באותה תיקייה.
- המפתח שמור רק כאן, בסוד `ELEVENLABS_API_KEY`. אף אפליקציה לא רואה אותו.
- כל קובץ זמין בכתובת:
  `https://mazivco-design.github.io/sounds/projects/<app>/<file>.mp3`

הסבר מלא לעבודה עם Claude נמצא ב-`CLAUDE.md`.
