import socket
import ssl
import re
import argparse
import sys
import time
import json
import os

DEFAULT_CONFIG = {
    "channel": "",
    "bot_name": "",
    "patterns": {
        "follow": "just followed!",
        "tip": "just tipped",
        "host": "just hosted the stream",
        "sub": "just subscribed!",
        "resub": "just subscribed for",
        "giftsub": "just gifted a subscription!",
        "bits": "cheered",
        "redeem": "just redeemed",
        "raid": "raids with",
        "order": "just ordered"
    },
    "instructions": {
        "follow": "Show appreciation by greeting {user} and thanking them for the follow.",
        "tip": "Acknowledge {user}'s donation of {amount} and express gratitude for their support.",
        "host": "Give a shout-out to {user} for hosting {channel}'s stream.",
        "sub": "Celebrate {user}'s subscription and give them a warm welcome.",
        "resub": "Acknowledge {user}'s loyalty of {months} months and express gratitude for their continued support.",
        "giftsub": "Acknowledge {user}'s generosity and express gratitude.",
        "bits": "Give a big thank you to {user} for the {amount} bits and mention their message.",
        "redeem": "Acknowledge {user}'s redemption of {reward} and fulfill their request if applicable.",
        "raid": "Welcome the raiding party and express appreciation to {user} for bringing {viewers} viewers.",
        "order": "Acknowledge {user}'s order for {item} and let them know when it will be fulfilled."
    }
}

def load_or_create_config(config_path='covas_twitch_config.json'):
    """Load existing config or create new one with defaults"""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all fields exist
                merged_config = DEFAULT_CONFIG.copy()
                if isinstance(config, dict):
                    merged_config.update(config)
                    # Ensure all sections exist
                    for section in ['patterns', 'instructions']:
                        if section not in merged_config:
                            merged_config[section] = DEFAULT_CONFIG[section]
                        elif isinstance(merged_config[section], dict):
                            # Ensure all events exist in each section
                            for key in DEFAULT_CONFIG[section]:
                                if key not in merged_config[section]:
                                    merged_config[section][key] = DEFAULT_CONFIG[section][key]
                return merged_config
        except (json.JSONDecodeError, IOError) as e:
            log(f"Error loading config: {str(e)}")
            return DEFAULT_CONFIG
    else:
        # Create new config file with defaults
        try:
            with open(config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG
        except IOError as e:
            log(f"Error creating config: {str(e)}")
            return DEFAULT_CONFIG

def parse_args():
    parser = argparse.ArgumentParser(description='COVAS:NEXT Twitch Integration - Event Detection Module')
    parser.add_argument('--channel', required=True, help='Twitch channel name')
    parser.add_argument('--bot-name', required=True, help='Bot name')
    parser.add_argument('--patterns', required=True, help='JSON string of event patterns and instructions')
    return parser.parse_args()

def log(message, is_debug=False):
    """Print message and flush stdout to ensure immediate output"""
    if not is_debug:  # Only print non-debug messages
        print(message, flush=True)

def create_pattern_matchers(config, channel_name):
    """Create regex patterns and their corresponding formatters based on configured patterns"""
    pattern_matchers = []
    
    # Define event patterns with their corresponding instruction formatters
    events = [
        ('follow', r"(.+) {pattern}", lambda m: (m[0],)),
        ('tip', r"(.+) {pattern} ([0-9]+)", lambda m: (m[0], m[1])),
        ('host', r"(.+) {pattern}", lambda m: (m[0],)),
        ('sub', r"(.+) {pattern}", lambda m: (m[0],)),
        ('resub', r"(.+) {pattern} ([0-9]+)", lambda m: (m[0], m[1])),
        ('giftsub', r"(.+) {pattern}", lambda m: (m[0],)),
        ('bits', r"(.+) {pattern} ([0-9]+)", lambda m: (m[0], m[1])),
        ('redeem', r"(.+) {pattern} (.+)", lambda m: (m[0], m[1])),
        ('raid', r"(.+) {pattern} ([0-9]+)", lambda m: (m[0], m[1])),
        ('order', r"(.+) {pattern} (.+)", lambda m: (m[0], m[1]))
    ]
    
    for event_key, pattern_template, group_formatter in events:
        try:
            pattern = pattern_template.format(pattern=config['patterns'][event_key])
            pattern_matchers.append((
                re.compile(pattern, re.IGNORECASE),
                lambda m, k=event_key, f=group_formatter: (k, f(m))
            ))
        except re.error as e:
            log(f"ERROR - Failed to compile pattern for {event_key}: {str(e)}")
            continue
    
    return pattern_matchers

def process_event(message, channel_name, pattern_matchers, config):
    """Process various Twitch events using configured patterns"""
    log(f"DEBUG - Checking message: {message}", True)
    
    for pattern, formatter in pattern_matchers:
        match = pattern.match(message)
        if match:
            event_key, groups = formatter(match.groups())
            instruction = config['instructions'][event_key]
            
            # Format instruction with captured groups
            format_args = {
                'user': groups[0],
                'channel': channel_name,
                'amount': groups[1] if len(groups) > 1 else '',
                'months': groups[1] if len(groups) > 1 else '',
                'viewers': groups[1] if len(groups) > 1 else '',
                'reward': groups[1] if len(groups) > 1 else '',
                'item': groups[1] if len(groups) > 1 else '',
                'message': groups[1] if len(groups) > 1 else ''
            }
            
            try:
                formatted_instruction = instruction.format(**format_args)
                log(f"INSTRUCTION: {formatted_instruction}")
                return True
            except KeyError as e:
                log(f"ERROR - Failed to format instruction: {str(e)}")
    
    return False

def main():
    args = parse_args()
    channel_name = args.channel.lower()
    if not channel_name.startswith('#'):
        channel_name = f"#{channel_name}"
    
    # Load configuration
    try:
        config = json.loads(args.patterns)
        # Verify config structure
        required_sections = ['patterns', 'instructions']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
    except json.JSONDecodeError:
        log("Error: Invalid configuration JSON")
        sys.exit(1)
    except ValueError as e:
        log(f"Error: {str(e)}")
        sys.exit(1)
    
    # Create pattern matchers
    pattern_matchers = create_pattern_matchers(config, args.channel)
    
    # Print minimal configuration
    log("Connecting to Twitch chat...")

    # Twitch IRC server details
    HOST = "irc.chat.twitch.tv"
    PORT = 443  # HTTPS port
    NICK = "justinfan" + str(int(time.time()))  # Anonymous connection with random number
    CHANNEL = channel_name

    # Connect to Twitch IRC
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Create socket and wrap with SSL
        sock = socket.socket()
        sock = context.wrap_socket(sock, server_hostname=HOST)
        sock.connect((HOST, PORT))
        
        # Send connection info for anonymous connection
        sock.send(f"NICK {NICK}\r\n".encode("utf-8"))
        sock.send(f"USER {NICK} 8 * :{NICK}\r\n".encode("utf-8"))
        sock.send(f"JOIN {CHANNEL}\r\n".encode("utf-8"))

        log("Successfully connected to chat!")

        while True:
            try:
                resp = sock.recv(2048).decode("utf-8")
                log(f"DEBUG - Raw message: {resp.strip()}", True)

                # Handle PING-PONG to keep the connection alive
                if resp.startswith("PING"):
                    sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                    continue

                # Extract username and message from chat
                chat_match = re.search(r":([^!]+)![^@]+@[^.]+\.tmi\.twitch\.tv PRIVMSG #[^:]+:(.+)", resp.strip())
                if chat_match:
                    username, message = chat_match.groups()
                    log(f"CHAT - {username}: {message}")
                    
                    # Process for special events
                    process_event(message, args.channel, pattern_matchers, config)

            except Exception as e:
                log(f"Error in message loop: {str(e)}")
                break

    except Exception as e:
        log(f"Connection error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
