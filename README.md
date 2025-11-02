# Whisparr Bridge

Whisparr Bridge is a [Stash](https://stashapp.cc/) plugin that mirrors scenes into [Whisparr](https://github.com/Whisparr/Whisparr/) as soon as their metadata links to a StashDB entry. When a scene update finishes inside Stash, the plugin looks for a matching StashDB ID and, if present, creates (or updates) the movie record in Whisparr using the defaults from your Whisparr instance.

## How It Works
 - When a scene is updated, if it has a stashid, the scene is added to whisparr and monitored.
 - Pairs nicely with [renamer](https://github.com/stash-of-awesomeness/stash-plugins) when configured correctly
 - Bulk identifies allow you to mass add files to whisparr

All HTTP requests include the Whisparr API key you provide in the plugin settings.

## Installation

1. Copy both `whisparr-bridge.py` and `whisparr-bridge.yml` into your Stash plugins directory (commonly `<stash-root>/whisparr-bridge/plugins`).
3. Install the Python dependency that ships with Stash plugins:
   ```bash
   pip install stashapp-tools
   ```
   The plugin relies on `stashapi` from this package for communicating with Stash.
4. Restart (or reload) Stash so it picks up the new plugin manifest.

## Configuration

Open the plugin settings inside Stash and populate the fields below:

| Setting | Description |
| --- | --- |
| `Whisparr URL` | Base URL to your Whisparr instance, e.g. `http://localhost:6969`. |
| `Whisparr API Key` | API key from Whisparr (`Settings → General → Security`). |
| `StashDB host match (e.g. stashdb.org)` | Substring used to identify the correct StashDB endpoint among a scene's external IDs. Defaults to `stashdb.org`. (Mainly for the future if whisparr adds more or custom stashboxes) |
| `Monitor after add (true/false)` | When `true`, new movies are monitored and Whisparr's `monitor` option is set to `movieOnly`; otherwise they stay unmonitored. |

### Whisparr Defaults

The script automatically fetches your first quality profile and root folder from Whisparr and uses them for every new movie. If you need different defaults, reorder or adjust these values within Whisparr.

## Troubleshooting

- **Missing settings**: The script logs an error if the URL or API key are blank. Double-check the plugin configuration inside Stash.
- **No StashDB ID**: Scenes without the configured endpoint substring are skipped silently; confirm the scene has a StashDB link that matches the substring.
- **Unexpected HTTP errors**: Review the Stash plugin log for status codes returned by Whisparr. You may need to adjust permissions or verify the API key.

## License

This project does not currently include an explicit license. Please open an issue or contact the author if you need clarification on usage rights.

