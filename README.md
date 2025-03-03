# COVAS:NEXT Twitch Integration

A bridge between Twitch live events and COVAS:NEXT, enabling AI-driven interactions in Elite: Dangerous based on your Twitch stream activity.

## Overview

This integration listens to Twitch chat events (follows, subs, tips, etc.) and forwards them to COVAS:NEXT, which then generates contextual AI responses in Elite: Dangerous. The system requires a Twitch bot account to post messages that trigger the responses.

## Quick Setup

1. **Requirements**
   - COVAS:NEXT running

2. **Configuration**
   - Enter your Twitch channel name
   - Enter your bot account name
   - Configure event patterns and instructions:
     - **Patterns**: What to match in chat (e.g., "!thanks {user} for the follow!")
     - **Instructions**: How COVAS:NEXT should respond (e.g., "Act grateful for {user}'s follow")

## Event Types

- Follows
- Subscriptions (new/resub)
- Bits
- Tips
- Raids
- Channel Point Redemptions
- Host/Raids
- Orders

Each event can be customized with unique patterns and AI instructions to create personalized interactions for your stream.

## Tips

- Test your patterns before going live (set your name as botname and write into your own chat to emulate notifications)
- Keep AI instructions clear and specific
- Use available variables in your templates (shown in the UI)
- Save your configuration before starting the bot

## Note

Remember to have your bot post messages in chat - the integration listens for these messages to trigger COVAS:NEXT responses.