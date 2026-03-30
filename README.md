> [!WARNING]
> This project is a **prototype** and is not production-ready.

# Default Agent

An external replacement for the default [conversation][] agent in Home Assistant.

## Usage

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

## How it Works

This project replicates the behavior of the default Assist agent in Home Assistant. When a new command comes in, this agent:

1. Fetches information about [exposed entities][], areas, and floors from Home Assistant
2. Finds the best intent match for the command text using [hassil][]
    - Command sentences come from the [home-assistant-intents][] package, [custom sentences](#custom-sentences), or a [development version of the intents repository](#intents-development)
3. Matches names with entities/areas/floors in [`async_match_targets`](default_agent/name_matcher.py)
4. Locates an [intent handler](default_agent/intents) for the matched intent
5. Executes the appropriate [actions][] in the intent handler
6. Returns a response to the user

## Timers

For timers to work, you will need to install a [HACS integration][mike-voice-hacs] that adds the appropriate websocket commands.

## Custom Sentences

Just like in Home Assistant, [custom sentences][] can be used by passing `--custom-sentences /path/to/custom_sentences` to the server. This should contain `<language>/<sentences>.yaml` files, such as `en/my_sentences.yaml`.

If you just want to use custom sentences, the `--no-builtin-intents` option will disable loading the built-in intents.

### Custom Responses

Responses can also be overridden in a custom sentences file. For example, adding this YAML to a file like `en/my_sentences.yaml` will override the response for when lights are turned on in a specific area:

``` yaml
language: en
responses:
  intents:
    HassTurnOn:
      lights_area: "Turn on the lights in the {{ slots.area }}"
```

See the `responses` directory of the [intents][] repository for a list of available responses.

## Intents Development

You can work on a development version of the [intents][] repo by passing `--intents-repo /path/to/intents` to the server. This will load intents from the repo instead of using the built-in `home-assistant-intents` package.

## Disabling Intents

You may disable specific intents by using `--disable-intent <intent>`. These intents will not be loaded (either from built-in intents or your custom sentences), and therefore cannot be matched.

## Future Plans

Ideas for the future of this project:

- A web interface that allows users to:
    - Test and debug sentences and intent handlers
    - Enable/disable intents (per area or satellite?)
    - Enable/disable specific intent [slot combinations][]. For example, users could allow the lights to be turned on/off in the current area, but not other areas by name.
- The addition of fuzzy command matching via [sentence transformers][]
- Make entity exposure more fine-grained, so some entities are only exposed to specific satellites
- Add both long and short responses, and allow users to configure which are used and when
- Allow custom intents that can use parts of Home Assistant's [script syntax][] to execute their actions (no Python needed)
- Make name matching more customizable. For example, having "turn on kitchen lights" match "turn on {area} lights" before "turn on {name}"


<!-- Links -->
[hassil]: https://github.com/home-assistant/hassil
[intents]: https://github.com/OHF-Voice/intents
[custom sentences]: https://www.home-assistant.io/voice_control/custom_sentences_yaml#setting-up-sentences-in-the-config-directory
[mike-voice-hacs]: https://github.com/synesthesiam/mike-voice-hacs
[conversation]: https://www.home-assistant.io/integrations/conversation
[exposed entities]: https://www.home-assistant.io/voice_control/voice_remote_expose_devices
[actions]: https://www.home-assistant.io/docs/scripts/perform-actions
[home-assistant-intents]: https://pypi.org/project/home-assistant-intents
[slot combinations]: https://github.com/OHF-Voice/intents/blob/main/docs/slot_combinations.md
[sentence transformers]: https://github.com/OHF-Voice/sentence-transformers-agent
[script syntax]: https://www.home-assistant.io/docs/scripts
