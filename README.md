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
   - Configure event patterns and instructions using the templates below

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
- **Pattern**: `{user} cheered {amount} bits! {message}`
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

## Tips

- Test your patterns before going live (set your name as botname and write into your own chat to emulate notifications)
- Keep AI instructions clear and specific
- Use available variables in your templates (shown in the UI)
- Save your configuration before starting the bot

## Note

Remember to have your bot post messages in chat - the integration listens for these messages to trigger COVAS:NEXT responses.