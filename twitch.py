import socket
import ssl
import re
import argparse
import sys
import time
import json
import os
from EDMesg.base import EDMesgEvent
from EDMesg.TwitchIntegration import create_twitch_provider, TwitchNotificationEvent
from EDMesg.CovasNext import ExternalChatNotification, ExternalBackgroundChatNotification, create_covasnext_client

DEFAULT_CONFIG = {
    "channel": "",
    "bot_name": "",
    "openai_verification": False,
    "openai_api_key": "",
    "patterns": {
        "follow": "{user} just followed!",
        "tip": "{user} just tipped {amount}! Message: {message}",
        "host": "{user} just hosted the stream for {viewers} viewers!",
        "sub": "{user} just subscribed!",
        "resub": "{user} just subscribed for {months} months in a row!",
        "giftsub": "{user} just gifted a subscription!",
        "bits": "{user} cheered {amount} bits! Message: {message}",
        "redeem": "{user} just redeemed {reward}!",
        "raid": "{user} raids with {viewers} viewers!",
        "order": "{user} just ordered {item}!"
    },
    "instructions": {
        "follow": "Show appreciation by greeting {user} and thanking them for the follow.",
        "tip": "Acknowledge {user}'s donation of {amount}, express gratitude for their support and mention their message: {message}",
        "host": "Give a shout-out to {user} for hosting the stream and thank them for bringing {viewers} viewers.",
        "sub": "Celebrate {user}'s subscription and give them a warm welcome.",
        "resub": "Acknowledge {user}'s loyalty of {months} months and express your gratitude for their continued support.",
        "giftsub": "Acknowledge {user}'s generosity and express your gratitude.",
        "bits": "Give a big thank you to {user} for the {amount} bits and mention their message: {message}",
        "redeem": "Acknowledge {user}'s redemption of {reward} and fulfill their request if applicable.",
        "raid": "Welcome the raiding party of {viewers} viewers and express your appreciation to {user} for the raid.",
        "order": "Acknowledge {user}'s order of {item} and let them know when it will be fulfilled."
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
    parser.add_argument('--openai-verification', action='store_true', help='Enable OpenAI verification')
    parser.add_argument('--openai-api-key', help='OpenAI API key')
    return parser.parse_args()

def log(message, is_debug=False):
    """Print message and flush stdout to ensure immediate output"""
    if not is_debug:  # Only print non-debug messages
        timestamp = time.strftime("%H:%M")
        print(f"{message}", flush=True)

def create_pattern_matchers(config, channel_name):
    """Create regex patterns and their corresponding formatters based on configured patterns"""
    pattern_matchers = []
    
    # Define event types and their variable groups
    events = {
        'follow': ['user'],
        'tip': ['user', 'amount', 'message'],
        'host': ['user', 'viewers'],
        'sub': ['user'],
        'resub': ['user', 'months'],
        'giftsub': ['user'],
        'bits': ['user', 'amount', 'message'],
        'redeem': ['user', 'reward'],
        'raid': ['user', 'viewers'],
        'order': ['user', 'item']
    }
    
    for event_key, variables in events.items():
        try:
            pattern = config['patterns'][event_key]
            regex_pattern = re.escape(pattern)
            
            for var in variables:
                placeholder = re.escape('{' + var + '}')
                if var in ['amount', 'viewers', 'months']:
                    regex_pattern = regex_pattern.replace(placeholder, r'(\d+(?:\.\d+)?|\d+)')
                else:
                    regex_pattern = regex_pattern.replace(placeholder, r'(.+?)')
            
            regex_pattern = f"^{regex_pattern}$"
            
            def make_formatter(key, num_vars):
                return lambda m: (key, tuple(m.group(i+1) for i in range(num_vars)))
            
            pattern_matchers.append((
                re.compile(regex_pattern, re.IGNORECASE),
                make_formatter(event_key, len(variables))
            ))
            
        except (KeyError, re.error) as e:
            log(f"ERROR - Failed to create pattern for {event_key}: {str(e)}")
            continue
    
    return pattern_matchers

def process_event(username, message, channel_name, pattern_matchers, config, covasnext_client):
    """Process various Twitch events using configured patterns"""
    # Log OpenAI verification status and API key presence
    log(f"OpenAI Verification: {'Enabled' if config.get('openai_verification', False) else 'Disabled'}")
    log(f"OpenAI API Key: {'Configured' if config.get('openai_api_key') else 'Not Configured'}")
    
    # Check for immediate reaction first
    immediate_reaction = config.get('immediate_reaction', '')
    if immediate_reaction and immediate_reaction in message:
        log(f"IMMEDIATE REACTION - {username}: {message}", True)
        covasnext_client.publish(
            ExternalChatNotification(
                service='twitch',
                username=config['bot_name'],
                text=f"Reply to twitch message from {username}: {message}"
            )
        )
    else:
        log(f"CHAT - {username}: {message}")
        covasnext_client.publish(
            ExternalBackgroundChatNotification(
                service='twitch',
                username=username,
                text=message
            )
        )

    if username.lower() == config['bot_name'].lower():
        for pattern, formatter in pattern_matchers:
            try:
                match = pattern.match(message)
                if match:
                    event_key, groups = formatter(match)
                    instruction = config['instructions'][event_key]
                    
                    # Format instruction with captured groups
                    format_args = {
                        'user': groups[0],
                        'channel': channel_name
                    }
                    
                    # Add additional parameters based on event type
                    if event_key in ['tip', 'bits']:
                        format_args.update({
                            'amount': groups[1],
                            'message': groups[2]
                        })
                    elif event_key in ['host', 'raid']:
                        format_args['viewers'] = groups[1]
                    elif event_key == 'resub':
                        format_args['months'] = groups[1]
                    elif event_key == 'redeem':
                        format_args['reward'] = groups[1]
                    elif event_key == 'order':
                        format_args['item'] = groups[1]
                    
                    try:
                        formatted_instruction = instruction.format(**format_args)
                        log(f"INSTRUCTION: {formatted_instruction}")
                        
                        # Send instruction to EDMesg using TwitchNotificationEvent
                        try:
                            covasnext_client.publish(
                                ExternalChatNotification(
                                    service='twitch',
                                    username=config['bot_name'],
                                    text=formatted_instruction
                                )
                            )
                            log(f"Sent instruction to EDMesg: {formatted_instruction}")
                        except Exception as e:
                            log(f"Error sending to EDMesg: {str(e)}")
                        
                        return True
                    except KeyError as e:
                        log(f"ERROR - Failed to format instruction: {str(e)}")
                else:
                    # Debug output for non-matching patterns
                    log(f"DEBUG - Pattern '{pattern.pattern}' did not match message: {message}", True)
            except Exception as e:
                log(f"ERROR - Pattern matching failed: {str(e)}", True)
        
    return False

def main():
    args = parse_args()
    channel_name = args.channel.lower()
    if not channel_name.startswith('#'):
        channel_name = f"#{channel_name}"
    
    try:
        config = json.loads(args.patterns)
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
    
    pattern_matchers = create_pattern_matchers(config, args.channel)
    
    log(f"Channel: {args.channel}")
    log(f"Bot Name: {args.bot_name}")

    # Initialize notification clients
    covasnext_client = create_covasnext_client()

    HOST = "irc.chat.twitch.tv"
    PORT = 443
    NICK = "justinfan" + str(int(time.time()))
    CHANNEL = channel_name

    try:
        context = ssl.create_default_context()
        sock = socket.socket()
        sock = context.wrap_socket(sock, server_hostname=HOST)
        sock.connect((HOST, PORT))
        
        sock.send(f"NICK {NICK}\r\n".encode("utf-8"))
        sock.send(f"USER {NICK} 8 * :{NICK}\r\n".encode("utf-8"))
        sock.send(f"JOIN {CHANNEL}\r\n".encode("utf-8"))

        log("Connected successfully")

        while True:
            try:
                resp = sock.recv(2048).decode("utf-8")

                if resp.startswith("PING"):
                    sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                    continue

                chat_match = re.search(r":([^!]+)![^@]+@[^.]+\.tmi\.twitch\.tv PRIVMSG #[^:]+:(.+)", resp.strip())
                if chat_match:
                    username, message = chat_match.groups()
                    process_event(username, message, args.channel, pattern_matchers, config, covasnext_client)

            except Exception as e:
                log(f"Error in message loop: {str(e)}")
                break

    except Exception as e:
        log(f"Connection error: {str(e)}")
    finally:
        # Clean up notification clients
        try:
            covasnext_client.close()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
