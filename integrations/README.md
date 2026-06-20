# Integrations

External-system adapters behind abstraction interfaces (provider choice is configuration, not code).

- `notifications/` — `email-ses` (AWS SES), `sms-msg91` (MSG91), `whatsapp-meta` (Meta WhatsApp Business API), `push-fcm` (Firebase Cloud Messaging).
- `eway-bill/`, `gst/` — India-first tax/compliance integrations.

Interfaces and adapters are implemented in later sprints (notifications in S3, GST/e-way in S8).
