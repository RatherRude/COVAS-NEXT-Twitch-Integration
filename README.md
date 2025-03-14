# COVAS:NEXT Twitch Integration

A bridge between Twitch live events and COVAS:NEXT, enabling AI-driven interactions in Elite: Dangerous based on your Twitch stream activity.

## Overview

This integration listens to Twitch chat events (follows, subs, tips, bits, etc.) and forwards them to COVAS:NEXT, which then generates contextual AI responses in Elite: Dangerous. Regular chat messages are also included in the LLM context, allowing the AI to develop an understanding of ongoing conversations and naturally react to discussions, jokes, and commands from the audience.

The system features a graphical interface for configuring event patterns, custom responses, and AI behavior, enabling a seamless, immersive experience. By dynamically adapting to both chat reactions and game events, COVAS:NEXT enhances interactivity, making the AI feel like an active crew member aware of both the game and the Twitch chat.

## Features

- **Easy-to-use GUI** for configuration and bot management
- **Real-time pattern matching** for Twitch events
- **Content moderation** using OpenAI's moderation API
- **Immediate reaction** to specific chat messages
- **Background processing** of all chat messages
- **Customizable patterns and instructions** for all event types

## Setup and Installation

1. **Requirements**
   - COVAS:NEXT must be running

2. **Running the Application**
   - Double-click the executable (Windows) found in the UI folder

## Configuration

### Basic Settings

- **Twitch Channel**: The channel name you want to monitor
- **Bot Name**: The name of the bot that will post event messages in your chat
- **OpenAI Verification**: Enable to use OpenAI's moderation API to check message content
- **OpenAI API Key**: Your OpenAI API key (required if verification is enabled)
- **Immediate Reaction Message**: Text that will trigger an immediate response when found in chat messages (default: @COVAS)

### Event Settings

For each event type, you can configure:
- **Pattern**: The message format to match in chat
- **Instruction**: What COVAS:NEXT should do when the pattern is matched

## Default Event Templates

### Follow
- **Pattern**: `{user} just followed!`
- **Variables**: `{user}`
- **Instruction**: `Show appreciation by greeting {user} and thanking them for the follow.`

### Tip
- **Pattern**: `{user} just tipped {amount}! Message: {message}`
- **Variables**: `{user}, {amount}, {message}`
- **Instruction**: `Acknowledge {user}'s donation of {amount}, express gratitude for their support and mention their message: {message}`

### Host
- **Pattern**: `{user} just hosted the stream for {viewers} viewers!`
- **Variables**: `{user}, {viewers}`
- **Instruction**: `Give a shout-out to {user} for hosting the stream and thank them for bringing {viewers} viewers.`

### Subscribe
- **Pattern**: `{user} just subscribed!`
- **Variables**: `{user}`
- **Instruction**: `Celebrate {user}'s subscription and give them a warm welcome.`

### Resub
- **Pattern**: `{user} just subscribed for {months} months in a row!`
- **Variables**: `{user}, {months}`
- **Instruction**: `Acknowledge {user}'s loyalty of {months} months and express gratitude for their continued support.`

### Gift Sub
- **Pattern**: `{user} just gifted a subscription!`
- **Variables**: `{user}`
- **Instruction**: `Acknowledge {user}'s generosity and express gratitude.`

### Bits
- **Pattern**: `{user} cheered {amount} bits! Message: {message}`
- **Variables**: `{user}, {amount}, {message}`
- **Instruction**: `Give a big thank you to {user} for the {amount} bits and mention their message: {message}`

### Channel Point Redemption
- **Pattern**: `{user} just redeemed {reward}!`
- **Variables**: `{user}, {reward}`
- **Instruction**: `Acknowledge {user}'s redemption of {reward} and fulfill their request if applicable.`

### Raid
- **Pattern**: `{user} raids with {viewers} viewers!`
- **Variables**: `{user}, {viewers}`
- **Instruction**: `Welcome the raiding party and express appreciation to {user} for bringing {viewers} viewers.`

### Order
- **Pattern**: `{user} just ordered {item}!`
- **Variables**: `{user}, {item}`
- **Instruction**: `Acknowledge {user}'s order for {item} and let them know when it will be fulfilled.`

## How It Works

1. Start the application and configure your settings
2. Click "Start Bot" to begin monitoring chat
3. When your bot posts a message in chat that matches one of your configured patterns, COVAS:NEXT will generate a response
4. All chat messages are also processed in the background for AI context
5. Messages containing the "immediate reaction" text trigger a direct response

## Advanced Features

### OpenAI Moderation

When enabled, all chat messages are checked using OpenAI's moderation API before processing. This helps filter out inappropriate content before it reaches COVAS:NEXT. This is free.

### Immediate Reaction

Configure a trigger phrase (default: @COVAS) that will cause COVAS:NEXT to respond immediately to a message when detected in chat.

### Background Chat Processing

All chat messages are sent to COVAS:NEXT as background context, allowing the AI to have awareness of ongoing conversations.

## Troubleshooting

- **Bot Not Connecting**: Make sure your channel name is correct
- **Patterns Not Matching**: Check your pattern syntax against example messages
- **OpenAI Verification Errors**: Verify your API key is correct

## Notes

- The application saves your configuration automatically
- You can reset to default settings at any time
- Make sure your bot is posting messages in chat that match your configured patterns
- Test your patterns before going live, the integration will react to the channel owner's and the bot's messages.
