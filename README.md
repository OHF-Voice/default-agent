> [!WARNING]
> This project is a **prototype** and is not production-ready.

# Default Agent

An external replacement for the default [conversation](https://www.home-assistant.io/integrations/conversation/) agent in Home Assistant.

## Usage

This depends on a development version of Home Assistant, including a yet-to-be-merged [PR](https://github.com/home-assistant/core/pull/164765).

Install with:

``` python
pip install 'default-agent@https://github.com/OHF-Voice/default-agent/archive/refs/heads/main.tar.gz'
```

Run with:

``` sh
python -m default_agent \
    --uri 'tcp://0.0.0.0:10500' \
    --hass-api 'http://homeassistant.local:8123/api' \
    --hass-token '<long-lived HA access token>'
```

You can now go to Home Assistant and add a Wyoming integration with the host/port of the default agent server (port 10500 was used in the example).

Create a voice assistant pipeline with the discovered conversation agent, and ensure that "Prefer local intents" is off.

Add `--debug` for more logging.

## Timers

For timers to work, you will need to install a [HACS integration](https://github.com/synesthesiam/mike-voice-hacs) that adds the appropriate websocket commands.

## Intents Development

You can work on a development version of the [intents](https://github.com/OHF-Voice/intents) repo by passing `--intents-repo /path/to/intents` to the server. This will load intents from the repo instead of using the built-in `home-assistant-intents` package.


## Custom Sentences

Just like in Home Assistant, [custom sentences](https://www.home-assistant.io/voice_control/custom_sentences_yaml#setting-up-sentences-in-the-config-directory) can be used by passing `--custom-sentences /path/to/custom_sentences` to the server. This should contain `<language>/<sentences>.yaml` files, such as `en/my_sentences.yaml`.

If you just want to use custom sentences, the `--no-builtin-intents` option will disable loading the built-in intents.

## Disabling Intents

You may disable specific intents by using `--disable-intent <intent>`. These intents will not be loaded (either from built-in intents or your custom sentences), and therefore cannot be matched.

